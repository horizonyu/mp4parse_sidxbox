import zipfile
from bs4 import BeautifulSoup
from io import BytesIO
from ebml import *


def get_video_file(content, attr, index):
    # global condition, file_path, video
    condition = []
    file_path = ''
    video = ''
    index += 1
    if attr == 'video':
        condition = ['video/webm', 'video/mp4']
    elif attr == 'audio':
        condition = ['audio/mp4']
    soup = BeautifulSoup(content, "lxml")
    tables = soup.findAll('table')
    tab = tables[0]
    exit_flag = False
    for tr in tab.findAll('tr'):
        for td in tr.findAll('td'):
            if td.getText() in condition:
                index -= 1
                if index == 0:
                    exit_flag = True
                    video = td.getText()
                    break
        if exit_flag:
            links = tr.findAll('a')
            file_path = links[1].get('href')
            break
    return file_path, video


def parse_mp4(data):
    # print('data: ',data)
    step = 0
    begin = data.find(b'sidx')
    print('begin: ', begin)
    print(data[begin+24:begin+28])
    count, = struct.unpack('!i', data[begin+24:begin+28])
    print('count: ', count)
    timescale, = struct.unpack('!i', data[(begin + 12): (begin+16)])
    i = 0
    while i < count:
        size, = struct.unpack('!i', data[(begin+28+i*12):(begin+28+i*12+4)])
        duration, = struct.unpack('!i', data[(begin + 32 + i*12):(begin + 36+i*12)])
        time = duration / timescale
        print(i, ':',size, '%.5f' % time )
        i+=1

    # print(data[410:420])
    # if data[begin + 6] == 14:
    #     step = 12
    # elif data[begin + 6] == 15:
    #     step = 16
    # elif data[begin + 6] == 6:
    #     step = 8
    # elif data[begin + 6] == 2:
    #     step = 4
    #
    # count,  = struct.unpack('!i', data[begin + 8: begin + 12])
    # samples = data[begin + 16: begin + 16 + count * step]
    # print('step: ', step)
    # print('samples: ', samples)
    # print('count: ', count)
    #
    # i = 0
    # total = data.find(b'mdat') - data.find(b'moof') + 8
    # print(data.find(b'mdat'))
    # print(data.find(b'moof'))
    # print('total: ', total)
    #
    # while i < count:
    #     print(samples[0 + i * step: 4 + i * step])
    #     size= struct.unpack('!i', samples[0 + i * step: 4 + i * step])
    #     total += size
    #     i += 1
    #     print('%d: %d' % (i, total))


def parse_webm(data):
    start = data.find(b'\x1F\x43\xB6\x75')
    stream = BytesIO(data[start:])
    len_of_data = len(data) - start

    i = 0
    while stream.tell() < len_of_data:
        id, _ = read_element_id(stream)
        size, _ = read_element_size(stream)
        if id == 524531317:  # CLUSTER
            pass
        elif id == 231:  # TimeCode
            read_unicode_string(stream, size)
        elif id == 163:  # SimpleBlock
            i += 1
            read_unicode_string(stream, size)
            print("%d: %d" % (i, stream.tell()))


if __name__ == '__main__':
    saz_file = zipfile.ZipFile('108p_video.saz', 'r')
    print(saz_file)
    path, type = get_video_file(saz_file.read('_index.htm'), 'video', 0)
    print(path, type)
    data = saz_file.read(path.replace('\\', '/'))

    if type == 'video/webm':
        print((data))
        parse_webm(data)
    elif type == 'video/mp4':
        print((data))
        parse_mp4(data)
    elif type == 'audio/mp4':
        print((data))
        parse_mp4(data)
