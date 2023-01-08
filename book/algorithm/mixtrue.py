import operator

from .item_cf import recommend_by_item_cf
from .user_cf import recommend_by_user_cf
from ..models import Book


def recommend_by_mixture(user_id, n=15, topk=10, w=0.8):
    # 混合推荐算法
    # 推荐列表 = w*P_cu + (1-w)* p_cf
    cu_list = recommend_by_user_cf(user_id, n, topk)  # 用户协同过滤得到的推荐列表
    cf_list = recommend_by_item_cf(user_id, n, topk)  # 物品协同过滤得到的推荐列表
    if not cu_list:
        # 用户协同过滤推荐列表为空
        if not cf_list:
            book_list = Book.objects.all().order_by("-sump")[:topk]
        else:
            # 返回物品协同过滤列表中的书籍
            book_list = Book.objects.filter(id__in=[s[0] for s in cf_list]).order_by("sump")[:topk]
    else:
        if not cf_list:
            # 物品协同过滤列表为空，则返回用户协同过滤列表中的书籍
            book_list = Book.objects.filter(id__in=[s[0] for s in cu_list]).exclude(
                id=user_id).order_by("-sump")[:topk]
        else:
            # 混合推荐
            rank = {}
            for book_id, distance in cu_list:
                cf_d = 0
                # 找到物品协同过滤列表中同一本书籍的兴趣度
                for book_id_cf, value in cf_list:
                    if book_id == book_id_cf:
                        cf_d = value
                        break

                rank[book_id] = w * distance + (1 - w) * cf_d
            rank_list = sorted(rank.items(), key=operator.itemgetter(1), reverse=True)[:topk]

            book_list = Book.objects.filter(id__in=[s[0] for s in rank_list]).exclude(
                id=user_id).order_by("-sump")[:topk]

    return book_list
