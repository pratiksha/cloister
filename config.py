import util

class CloisterConfig:
    def __init__(self, d):
        util.dict_to_obj(self, d)

    def __str__(self):
        return '\n'.join([k + ': ' + str(v) for k, v in self.__dict__.items()])
