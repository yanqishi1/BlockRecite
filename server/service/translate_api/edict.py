from server.service.translate_api.ECDICT.stardict import StarDict,DictCsv


if __name__ == '__main__':

    ecdict = DictCsv("D:\DL\BlockRecite\server\service\translate_api\ECDICT\ecdict.csv")

    print(ecdict.query("work"))