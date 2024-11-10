import xml.etree.ElementTree as ET
import re
import subprocess
import os

class MameInfo:
    def __init__(self, version, games):
        self.version = version
        self.games = games

class GameInfo:
    def __init__(self, name, title, version):
        self.name = name
        self.title = title
        self.title_lower = title.lower()
        self.version = version
        self.version_lower = version.lower()
        self.vers = split_version(version.lower())
        self.title_ch = ""

work_dir = ".mame_lang"
out_dir = "MxUI v1.5.2/lang/Chinese_Simplified"

def parse_gamelist(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        mame_version = None
        games = []
        for line in file:
            if line.startswith('<mame'):
                # 解析版本号
                root = ET.fromstring(line + "</mame>")
                mame_version = root.get('build')
            elif line.startswith('	<machine'):
                # 解析游戏信息
                game_root = ET.fromstring(line + "</machine>")
                game_name = game_root.get('name')
                game_desc = ET.fromstring(file.readline().strip()).text.strip()
                
                # 拆分游戏标题和补充说明
                titles = split_title(game_desc)
                game_title = titles[0].strip()
                if len(titles) == 3:
                    game_version = titles[1] + titles[2]
                else:
                    game_version = ""
    
                game = GameInfo(game_name, game_title, game_version)
                games.append(game)
    return MameInfo(mame_version, games)

def parse_dic_file(filename):
    results = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            if line == "":
                break
            else:
                results[line.strip().lower()] = file.readline().strip()
    return results

def parse_lang_file(filename):
    results = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            # 使用制表符分割每一行
            parts = line.strip().split('\t')
            if len(parts) == 3:
                name, desc, _ = parts
                # 拆分游戏标题和补充说明
                game_title = split_title(desc)
                game_title = game_title[0].strip()
                results[name] = game_title
    return results

def split_version(version_str):
    # 定义正则表达式
    pattern = re.compile(r'[\(\),\[\]]')

    # 分割字符串并生成数组
    result = [part for part in pattern.split(version_str) if part]
    return result

def split_title(desc_str):
    # 定义正则表达式
    pattern = re.compile(r'([\[\(])')

    # 使用正则表达式进行分割
    result = pattern.split(desc_str, maxsplit=1)
    return result

def save_lang_dic(mame_info, cn_dics, bootleg_dics):
    pattern = re.compile(r'set (\d+)', re.IGNORECASE)
    sorted_keys = sorted(bootleg_dics.keys(), key=lambda x: len(x), reverse=True)
    not_trans = []
    # 将游戏标题逐行写入到文件中
    with open(out_dir + '/mame_cn.lst', 'w', encoding='gbk') as file:
        for game in mame_info.games:
            if game.title_lower in cn_dics:
                title = cn_dics[game.title_lower].replace('\xa3', "")
                version = game.version.replace('\xa3', "").replace("[BET]", "[博彩]")
                for bootleg in sorted_keys:
                    version = re.sub(bootleg, bootleg_dics[bootleg], version, flags=re.IGNORECASE)
                    version = pattern.sub(r'第 \1 套', version)
                try:
                    file.write(f'{game.name}\t{title} {version}\t{title} {version}\n')
                except Exception as e:
                    # 处理其他异常
                    print("发生异常：", e, title, version)
            elif game.title_lower not in not_trans:
                not_trans.append(game.title_lower)

    with open(work_dir + '/not_trans.txt', 'w', encoding='utf-8') as file:
        file.write("\n".join(not_trans))
    
    with open(out_dir + '/mame_cn.lst', 'r', encoding='gbk') as file:
        content = file.read()

    with open(out_dir + '/mame_cn_utf8.lst', 'w', encoding='utf-8') as file:
        file.write(content)
    

def save_title_lang(mame_info, cn_dics):
    dics = {}
    for game in mame_info.games:
        if game.name in cn_dics:
            dics[game.title_lower] = cn_dics[game.name]
        
    # 提取游戏标题并去重
    titles = set(game.title_lower for game in mame_info.games)

    # 按照长度和字母顺序排序
    titles = sorted(titles, key=lambda x: (x))

    versions = []

    for game in mame_info.games:
        versions.extend(game.vers)

    pattern = re.compile(r'[^0-9\W]')

    versions = sorted(set(versions), key=lambda x: (x))

    not_trans = []
    
    # 将游戏标题逐行写入到文件中
    with open(work_dir + '/base_trans.txt', 'w', encoding='utf-8') as file:
        for title in titles:
            if title in dics:
                file.write(f'{title}\n')
                file.write(f'{dics[title]}\n')
            else:
                not_trans.append(title)
    
    with open(work_dir + '/not_trans.txt', 'w', encoding='utf-8') as file:
        for title in not_trans:
            file.write(f'{title}\n')
            file.write(f'{title}\n')

    hack_titles = []

    with open(work_dir + '/vers_trans.txt', 'w', encoding='utf-8') as file:
        for version in versions:
            # 使用正则表达式进行匹配
            result = pattern.search(version)
            if result:
                if version.startswith("bootleg of"):
                    hack_titles.append(version.replace("bootleg of", "").strip())
                else:
                    file.write(f'{version}\n')
                    
    with open(work_dir + '/hack_trans.txt', 'w', encoding='utf-8') as file:
        for version in hack_titles:
            file.write(f'bootleg of {version}\n')
            if version in dics:
                file.write(f'盗版自 {dics[version]}\n')
            else:
                file.write(f'盗版自 {version}\n')

script_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(script_dir)

# 调用示例
filename = 'gamelist.271.xml'
mame_info = parse_gamelist(filename)
print(f'MAME版本号：{mame_info.version}')
print(f'游戏数量：{len(mame_info.games)}')
#filename = work_dir + '/dic_252.txt'
#cn_dics = parse_dic_file(filename)
# save_title_lang(mame_info, cn_dics)
title_dics = parse_dic_file(work_dir + "/base_trans.txt")
bootleg_dics = parse_dic_file(work_dir + "/hack_trans.txt")
print(f'已翻译：{len(title_dics)}')
# 调用示例
save_lang_dic(mame_info, title_dics, bootleg_dics)

subprocess.run(['MxUI v1.5.2\\MxUI.exe'], cwd="MxUI v1.5.2")