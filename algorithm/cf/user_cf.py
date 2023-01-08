import math
import os
import pickle
from collections import defaultdict
from operator import itemgetter

from loguru import logger
from tqdm import tqdm


class UserCF:
    """ 基于用户的协同过滤
    根据用户之前的喜好以及其他兴趣相近的用户的选择来给用户推荐物品。
    利用用户的群体行为来计算用户的相关性。
    计算用户相关性的时候我们就是通过对比他们对相同物品打分的相关度来计算的

    举例：
    --------+--------+--------+--------+--------+
            |   X    |    Y   |    Z   |    R   |
    --------+--------+--------+--------+--------+
        a   |   5    |    4   |    1   |    5   |
    --------+--------+--------+--------+--------+
        b   |   4    |    3   |    1   |    ?   |
    --------+--------+--------+--------+--------+
        c   |   2    |    2   |    5   |    1   |
    --------+--------+--------+--------+--------+
    a用户给X物品打了5分，给Y打了4分，给Z打了1分
    b用户给X物品打了4分，给Y打了3分，给Z打了1分
    c用户给X物品打了2分，给Y打了2分，给Z打了5分
    那么很容易看到a用户和b用户非常相似，但是b用户没有看过R物品，
    那么我们就可以把和b用户很相似的a用户打分很高的R物品推荐给b用户
    """

    def __init__(self, data, user_col: str = None, item_col: str = None):
        """ data为`DataFrame`
        :param data: 用户的历史行为数据
        :param user_col: 用户ID所在列名
        :param item_col: 物品ID所在列名
        """
        self.user_set = set()
        self.item_set = set()
        self.user_sim_dict = dict()
        self.user_interacted_num = defaultdict(int)
        self.item_interacted_num = defaultdict(int)  # 热门推荐时会用到

        item_user = data.groupby(item_col)[user_col].apply(list).reset_index()
        self.item_user_dict = dict(zip(item_user[item_col], item_user[user_col]))

        user_item = data.groupby(user_col)[item_col].apply(list).reset_index()
        self.user_item_dict = dict(zip(user_item[user_col], user_item[item_col]))

    def calculate_similarity_matrix(self):
        """ 计算物品相似度 """
        logger.info("Calculating User Similarity Matrix")
        for item, users in tqdm(self.item_user_dict.items()):
            self.user_set.update(users)
            self.item_set.add(item)
            self.item_interacted_num[item] += len(users)
            for user in users:
                self.user_interacted_num[user] += 1
                self.user_sim_dict.setdefault(user, {})
                for related_user in users:
                    if user == related_user:
                        continue
                    self.user_sim_dict[user].setdefault(related_user, 0)
                    # 活跃物品在计算用户之间相似度时，贡献小于非活跃用户
                    self.user_sim_dict[user][related_user] += 1 / math.log(1 + len(users))

        # 理论上，用户之间共现的物品越多，相似度越高，但是，活跃用户与很多用户之间的相似度都很高
        for i, related_users in tqdm(self.user_sim_dict.items()):
            for j, cij in related_users.items():
                self.user_sim_dict[i][j] = \
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
                for relate_user, user_smi_score in sorted(
                        self.user_sim_dict[user_id].items(), key=itemgetter(1), reverse=True)[:n]:
                    for candidate_item in self.user_item_dict[relate_user]:
                        rank[candidate_item] += user_smi_score

                rec_items = [item[0] for item in sorted(rank.items(), key=itemgetter(1), reverse=True)[:topk]]
                if hot_fill:
                    # 如果推荐的物品不够，用热门物品进行填充
                    rec_items += popular_items[:topk - len(rec_items)]
                user_rec[user_id] = rec_items

        return user_rec


def recommend_by_user_cf(users, data, n=50, topk=20, hot_fill=False, cache_path=None, save=False, **kwargs):
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, 'rb') as file:
            user_cf = pickle.loads(file.read())
            file.close()
    else:
        user_cf = UserCF(data, **kwargs)
        user_cf.calculate_similarity_matrix()
        if save and cache_path:
            user_cf_pkl = pickle.dumps(user_cf)
            output = open(cache_path, 'wb')
            output.write(user_cf_pkl)
            output.close()

    return user_cf(users, n, topk, hot_fill)
