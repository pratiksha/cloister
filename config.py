import util

class CloisterConfig:
    def __init__(self, d):
        util.dict_to_obj(self, d)

    def __str__(self):
        return '\n'.join([k + ': ' + str(v) for k, v in self.__dict__.items()])

    def get_latest_clamor_ami(self, client, tag='clamor'):
        print('getting images')
        images = client.images.filter(Owners=['self'])
        print('got images', len(list(images)))
        images = sorted(filter(lambda x: tag in x.name, images),
                        key=lambda x: util.parse_ami_date(x.creation_date),
                        reverse=True)
        print('sorted')
        self.ami = images[0].id
