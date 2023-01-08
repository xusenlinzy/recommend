import math
import os
import pickle
from collections import defaultdict
from operator import itemgetter

import pandas as pd
from loguru import logger
from tqdm import tqdm


class ItemCF:
    """ 基于物品的协同过滤
    1.构建⽤户–>物品的对应表
    2.构建物品与物品的关系矩阵(同现矩阵)
    3.计算物品相似度矩阵
    4.根据⽤户的历史记录，给⽤户推荐物品
    """

    def __init__(self, data, user_col: str = None, item_col: str = None, item2cate: dict = None):
        """ data为`DataFrame`或者字典`{user_id: items}`
        :param data: 用户的历史行为数据
        :param user_col: 用户ID所在列名
        :param item_col: 物品ID所在列名
        :param item2cate: 物品的类型字典
        """
        self.item2cate = item2cate

        self.user_set = set()
        self.item_sim_dict = dict()
        self.item_interacted_num = defaultdict(int)

        if isinstance(data, pd.DataFrame):
            user_item = data.groupby(user_col)[item_col].apply(list).reset_index()
            self.user_item_dict = dict(zip(user_item[user_col], user_item[item_col]))
        else:
            self.user_item_dict = data

    def calculate_similarity_matrix(self):
        """ 计算物品相似度 """
        logger.info("Calculating Item Similarity Matrix")
        for user, items in tqdm(self.user_item_dict.items()):
            self.user_set.add(user)
            for item in items:
                self.item_interacted_num[item] += 1
                self.item_sim_dict.setdefault(item, {})
                for related_item in items:
                    if item == related_item:
                        continue
                    self.item_sim_dict[item].setdefault(related_item, 0)

                    related_score = 1
                    if self.item2cate:
                        # 如果二者类别相同相似度更高
                        related_score *= 1 if self.item2cate.get(
                            item, None) == self.item2cate.get(related_item, None) else 0.8

                    # 活跃用户在计算物品之间相似度时，贡献小于非活跃用户
                    self.item_sim_dict[item][related_item] += related_score / math.log(1 + len(items))

        # 理论上，物品之间共现的用户越多，相似度越高，但是，热门物品与很多物品之间的相似度都很高
        for i, related_items in tqdm(self.item_sim_dict.items()):
            for j, cij in related_items.items():
                self.item_sim_dict[i][j] = \
                    cij / math.sqrt(self.item_interacted_num[i] * self.item_interacted_num[j])

    def __call__(self, users, n=50, topk=20, hot_fill=False):
        """ 物品召回 """
        logger.info(f"Starting ItemCF: ecall@{topk}-Near@{n}")
        popular_items = [val[0] for val in sorted(
            self.item_interacted_num.items(), key=lambda x: x[1], reverse=True)[:topk]]

        user_rec = {}
        for user_id in tqdm(users):
            # 新用户，直接推荐热门物品
            if user_id not in self.user_set:
                user_rec[user_id] = popular_items
            else:
                rank = defaultdict(int)
                his_items = self.user_item_dict[user_id]
                # 遍历用户历史交互物品
                for his_item in his_items:
                    # 选取与his_item相似度最高的n个物品
                    for candidate_item, item_smi_score in sorted(
                            self.item_sim_dict[his_item].items(), key=itemgetter(1), reverse=True)[:n]:
                        rank[candidate_item] += item_smi_score

                rec_items = [item[0] for item in sorted(rank.items(), key=itemgetter(1), reverse=True)[:topk]]
                if hot_fill:
                    # 如果推荐的物品不够，用热门物品进行填充
                    rec_items += popular_items[:topk - len(rec_items)]
                user_rec[user_id] = rec_items

        return user_rec


def recommend_by_item_cf(users, data, n=50, topk=20, hot_fill=False, cache_path=None, save=False, **kwargs):
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, 'rb') as file:
            item_cf = pickle.loads(file.read())
            file.close()
    else:
        item_cf = ItemCF(data, **kwargs)
        item_cf.calculate_similarity_matrix()
        if save and cache_path:
            item_cf_pkl = pickle.dumps(item_cf)
            output = open(cache_path, 'wb')
            output.write(item_cf_pkl)
            output.close()

    return item_cf(users, n, topk, hot_fill)
