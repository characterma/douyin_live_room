import datetime, time, re, os
import pandas as pd
from glob import glob
from loguru import logger
import zhconv
import sys
import copy

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")

# 设置value的显示长度为200，默认为50
pd.set_option('max_colwidth', 200)
# 显示所有列，把行显示设置成最大
pd.set_option('display.max_columns', None)
# 显示所有行，把列显示设置成最大
pd.set_option('display.max_rows', None)


class SentencePairMatch:
    def __init__(self, chat_file_path, audio_reply_path, audio_begin_timestamp_file_path):
        self.chat_file_path = chat_file_path
        self.audio_reply_path = audio_reply_path
        self.audio_begin_timestamp_file_path = audio_begin_timestamp_file_path
        self.audio_begin_time = self.get_audio_begin_fromtime

    @property
    def get_audio_begin_fromtime(self) -> datetime.datetime:
        """将 13 位整数的毫秒时间戳转化成本地普通时间 (字符串格式)
        :param timestamp: 13 位整数的毫秒时间戳 (1456402864242)
        :return: 返回字符串格式 {str}'2016-02-25 20:21:04.242000'
        """
        try:
            with open(self.audio_begin_timestamp_file_path) as f:
                time_stamp = float(f.read().strip())
                local_str_time = datetime.datetime.fromtimestamp(time_stamp / 1000.0)
                logger.debug(type(local_str_time))
            return local_str_time
        except:
            logger.error('time stamp format is exception')

    @staticmethod
    def replace_multiple_spaces(string: str) -> str:
        """
        replace mutiple spaces
        """
        return re.sub(' +', ' ', string)

    def chinese_traditional_characters_to_simple_characters(self, text: str) -> str:
        """
        convert chinese traditional characters to simple characters
        """
        if type(text) == str and len(text) > 0:
            text = zhconv.convert(text, 'zh-hans')
        else:
            return ""
        logger.debug(text)
        return text

    def calculate_audio_specific_time(self, millisecond: int) -> datetime.datetime:
        """
        audio begin time + millisecond
        """
        return self.audio_begin_time + datetime.timedelta(milliseconds=millisecond)

    def barrage_message_process(self) -> pd.DataFrame:
        """
        Format barrage messages, conversion str to dataframe
        """
        all_barrage_message = []
        with open(self.chat_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                ls = line.strip().split("\t")
                try:
                    current_time = datetime.datetime.fromtimestamp(float(ls[0]))
                    format_current_time = current_time.strftime('%Y-%m-%d %H:%M')
                    # logger.debug(f"current_time: {current_time},format_current_time: {format_current_time}, {ls[1:]}")
                    all_barrage_message.append([current_time, format_current_time, ls[1], ls[2]])
                except:
                    continue
        barrage_message_df = pd.DataFrame(all_barrage_message,
                                          columns=['accurate_time', 'fuzzy_time', 'user_info', 'message'])
        logger.debug(f"barrage_message_df: \n{barrage_message_df.dtypes}")
        return barrage_message_df

    def audio_repair_message_process(self) -> pd.DataFrame:
        """
        1、get audio repair message data,
        2、convert chinese traditional characters to simple characters，
        3、calculate audio start time and end time
        4、There may be a reply within one minute after the barrage， so audio begin time Reduce by one minute
        """
        audio_repair_message_df = pd.read_table(self.audio_reply_path)
        audio_repair_message_df['text'] = audio_repair_message_df['text'].map(
            self.chinese_traditional_characters_to_simple_characters)
        audio_repair_message_df['start_time'] = audio_repair_message_df['start'].map(self.calculate_audio_specific_time)
        audio_repair_message_df['end_time'] = audio_repair_message_df['end'].map(self.calculate_audio_specific_time)
        audio_repair_message_df['join_time'] = audio_repair_message_df['start_time'].map(
            lambda date: date.strftime('%Y-%m-%d %H:%M'))
        audio_repair_message_df_backup = copy.deepcopy(audio_repair_message_df)
        logger.info(f"audio_repair_message_df: {audio_repair_message_df.shape}")
        audio_repair_message_df_backup['join_time'] = audio_repair_message_df_backup['start_time'].map(
            lambda x: (x - datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M'))
        complete_audio_repair_message_df = pd.concat([audio_repair_message_df, audio_repair_message_df_backup], axis=0)
        logger.debug(audio_repair_message_df[['start_time', 'end_time', 'text']].head())
        return complete_audio_repair_message_df

    def filter_sentence(self):
        return

    def sentence_pair_match(self):
        return

    def __call__(self, *args, **kwargs) -> pd.DataFrame:
        """
        There may be a reply within one minute after the barrage
        """
        barrage_message_df = self.barrage_message_process()
        audio_repair_message_df = self.audio_repair_message_process()
        logger.info(
            f"barrage_message_df shape:{barrage_message_df.shape}, audio_repair_message_df: {audio_repair_message_df.shape}")
        complete_info = pd.merge(left=barrage_message_df, right=audio_repair_message_df, left_on="fuzzy_time",
                                 right_on="join_time", how='left')
        complete_info['boundary_time_point'] = complete_info['accurate_time'].map(
            lambda x: (x + datetime.timedelta(minutes=1)))
        complete_info = complete_info[(complete_info['accurate_time'] < complete_info['start_time']) & (complete_info['boundary_time_point'] > complete_info['end_time'])]
        print(complete_info[['accurate_time', 'fuzzy_time', 'message', 'join_time', 'text']].head())
        return complete_info


def apply_data_process(all_live_chat_save_path: str, export_merge_result_dir_path: str):
    for d in os.listdir(all_live_chat_save_path):
        live_id, part_time = d.split('_')[0], d.split("_")[-1]
        date_hour = part_time[:4] + "-" + part_time[4:6] + "-" + part_time[6:8] + ' ' + part_time[8:10]
        chat_file_path, audio_reply_path = os.path.join(os.path.join(all_live_chat_save_path, d),
                                                        "chats.txt"), os.path.join(
            os.path.join(all_live_chat_save_path, d), 'output.tsv')
        audio_begin_timestamp_file_path = os.path.join(os.path.join(all_live_chat_save_path, d), 'fromtime')
        complete_info = SentencePairMatch(chat_file_path, audio_reply_path, audio_begin_timestamp_file_path)()
        logger.info(date_hour)
        export_file_path = os.path.join(export_merge_result_dir_path, f"{d}.xlsx")
        complete_info.to_excel(export_file_path, index=False)


if __name__ == '__main__':
    all_live_chat_save_path = r"D:\project\liverscrapy\livescrapy-master-8a490d20541e961a10844c28bcc4fffea3eaf285\app\data"
    export_merge_result_dir_path = r'D:\project\liverscrapy\livescrapy-master-8a490d20541e961a10844c28bcc4fffea3eaf285\app\extract_QA\data'
    os.makedirs(export_merge_result_dir_path, exist_ok=True)
    apply_data_process(all_live_chat_save_path, export_merge_result_dir_path)
