import operator
from math import sqrt

from movie.models import Rate


class ItemCf:
    """ 基于物品协同算法来获取推荐列表
    1.构建⽤户–>物品的对应表
    2.构建物品与物品的关系矩阵(同现矩阵)
    3.通过求余弦向量夹角计算物品之间的相似度，即计算相似矩阵
    4.根据⽤户的历史记录，给⽤户推荐物品
    """

    def __init__(self, user_id):
        self.user_id = user_id  # 用户id

    def get_data(self):
        # 获取用户评分过的资讯
        rates = Rate.objects.all()
        if not rates:
            return False

        datas = {}
        for rate in rates:
            user_id = rates.user_id
            if user_id not in datas:
                datas.setdefault(user_id, {})
                datas[user_id][rate.movie.id] = rate.mark
            else:
                datas[user_id][rate.movie.id] = rate.mark

        return datas

    def similarity(self, data):
        # 1 构造物品：物品的共现矩阵
        N = {}  # 喜欢物品i的总⼈数
        C = {}  # 喜欢物品i也喜欢物品j的⼈数
        for user, item in data.items():
            for i, score in item.items():
                N.setdefault(i, 0)
                N[i] += 1
                C.setdefault(i, {})
                for j, scores in item.items():
                    if j != i:
                        C[i].setdefault(j, 0)
                        C[i][j] += 1

        # 2 计算物品与物品的相似矩阵
        W = {}
        for i, item in C.items():
            W.setdefault(i, {})
            for j, item2 in item.items():
                W[i].setdefault(j, 0)
                W[i][j] = C[i][j] / sqrt(N[i] * N[j])

        return W

    def recommand_list(self, data, similarity_matrix, user, n=15, topk=10):
        """ 根据⽤户的历史记录，给⽤户推荐物品
        :param data: 用户数据
        :param similarity_matrix: 相似矩阵
        :param user: 推荐的用户
        :param n: 相似的n个物品
        :param topk: 推荐物品数量
        :return: 推荐物品列表
        """
        rank = {}
        for i, score in data[user].items():  # 获得⽤户user历史记录，
            # 获得与物品i相似的n个物品
            for j, w in sorted(
                    similarity_matrix[i].items(), key=operator.itemgetter(1), reverse=True)[:n]:
                if j not in data[user].keys():  # 该相似的物品不在⽤户user的记录⾥
                    rank.setdefault(j, 0)
                    rank[j] += float(score) * w  # 预测兴趣度=评分*相似度

        return sorted(rank.items(), key=operator.itemgetter(1), reverse=True)[:topk]

    def recommendation(self, n=15, topk=10):
        """ 给用户推荐相似资讯 """
        data = self.get_data()
        if not data or self.user_id not in data:
            # 用户没有评分过任何资讯，就返回空列表
            return []

        W = self.similarity(data)  # 计算物品相似矩阵
        sort_rank = self.recommand_list(data, W, self.user_id, n, topk)  # 推荐
        return sort_rank


def recommend_by_item_cf(user_id, n=15, topk=15):
    return ItemCf(user_id).recommendation(n, topk)
