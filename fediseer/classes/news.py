from datetime import datetime

class News:

    FEDISEER_NEWS = [
    ]

    def get_news(self):
        '''extensible function from gathering nodes from extensing classes'''
        return(self.FEDISEER_NEWS)

    def sort_news(self, raw_news):
        # unsorted_news = []
        # for piece in raw_news:
        #     piece_dict = {
        #         "date": datetime.strptime(piece["piece"], '%y-%m-%d'),
        #         "piece": piece["news"],
        #     }
        #     unsorted_news.append(piece_dict)
        sorted_news = sorted(raw_news, key=lambda p: datetime.strptime(p["date_published"], '%Y-%m-%d'), reverse=True)
        return(sorted_news)

    def sorted_news(self):
        return(self.sort_news(self.get_news()))
