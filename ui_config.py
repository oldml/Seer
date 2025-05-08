import gradio as gr # 导入 Gradio 库，用于创建 Web UI
import configparser # 导入 configparser 库，用于读写 INI 配置文件
import os # 导入 os 库，用于操作系统相关功能，如文件路径检查
import sys # 导入 sys 库，用于访问与 Python 解释器相关的变量和函数
from main import Main # 从 main.py 文件导入 Main 类

main = Main() # 创建 Main 类的实例，用于后续调用其方法

# Constants (常量)
CONFIG_PATH = 'config.ini' # 定义配置文件的路径和名称
DEFAULT_CONFIG = { # 定义默认配置字典，用于在配置文件不存在时创建
    '账号信息': {'userid': '', 'password': ''}, # 账号信息部分
    '通用设置': { # 通用设置部分
        'capability_equipment': '装备1', # 能力装备默认值
        'capability_title': '称号1', # 能力称号默认值
        'self_destructing_elf': '帝皇之御', # 自爆精灵默认值
        'rebound_damage_elf': '六界神王', # 弹伤精灵默认值
        'mending_blade_elf': '圣灵谱尼' # 补刀精灵默认值
    },
    '日常设置': { # 日常设置部分，包含多个日常任务的开关
        'daily_check_in': '默认', # 日常签到
        'a': '默认', 'b': '默认', 'c': '默认', 'd': '禁止', # 其他日常任务开关
        'e': '默认', 'f': '默认', 'g': '禁止', 'h': '默认',
        'i': '禁止', 'j': '默认', 'k': '默认', 'l': '默认'
    }
}

def load_config(): # 加载配置文件的函数
    config = configparser.ConfigParser() # 创建 ConfigParser 对象
    if not os.path.exists(CONFIG_PATH): # 检查配置文件是否存在
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile: # 如果不存在，则创建并写入默认配置
            config.read_dict(DEFAULT_CONFIG) # 从字典读取默认配置
            config.write(configfile) # 将配置写入文件
    config.read(CONFIG_PATH, encoding='utf-8') # 读取配置文件内容
    return config # 返回配置对象

def save_config(config): # 保存配置文件的函数
    with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile: # 打开配置文件进行写入
        config.write(configfile) # 将配置对象的内容写入文件

def login_action(userid, token): # 处理登录操作的函数
    try:
        user_id_int = int(userid) # 将用户ID转换为整数
        return main.run(user_id_int, token) # 调用 main 对象的 run 方法执行登录逻辑
    except ValueError: # 捕获用户ID转换失败的异常
        return "用户ID必须是一个整数" # 返回错误提示

def save_user_settings(userid, password, capability_equipment, capability_title, # 保存用户设置的函数
                       self_destructing_elf, rebound_damage_elf, mending_blade_elf,
                       daily_check_in, a, b, c, d, e, f, g, h, i, j, k, l):
    config = load_config() # 加载当前配置

    # 更新账号信息
    config['账号信息']['userid'] = str(userid)
    config['账号信息']['password'] = str(password)

    # 更新通用设置
    config['通用设置']['capability_equipment'] = str(capability_equipment)
    config['通用设置']['capability_title'] = str(capability_title)
    config['通用设置']['self_destructing_elf'] = str(self_destructing_elf)
    config['通用设置']['rebound_damage_elf'] = str(rebound_damage_elf)
    config['通用设置']['mending_blade_elf'] = str(mending_blade_elf)

    # 更新日常设置
    daily_settings_values = [daily_check_in, a, b, c, d, e, f, g, h, i, j, k, l] # 将所有日常设置的值收集到一个列表中
    # 遍历日常设置的键和对应的值，并更新到配置对象中
    for key, value in zip(config['日常设置'].keys(), daily_settings_values):
        config['日常设置'][key] = str(value)

    save_config(config) # 保存更新后的配置到文件
    return "设置已保存！" # 返回保存成功的提示

def restart_program(): # 重启程序的函数
    # 使用当前的Python解释器来执行一个新的程序实例，并替换当前的进程
    # 这会有效地重启应用程序
    os.execl(sys.executable, sys.executable, *sys.argv)


def create_ui(): # 创建 Gradio 用户界面的函数
    config = load_config() # 加载配置，用于初始化界面控件的默认值
    # 使用 gr.Blocks 创建一个 Gradio 应用块，设置主题和标题
    with gr.Blocks(theme = gr.themes.Soft(primary_hue = "sky", secondary_hue = "slate", neutral_hue = "slate"), title = '赛尔号台服小助手') as demo:

        gr.Markdown('# **赛尔号台服脱机小助手**') # 添加一个 Markdown 标题

        with gr.Tab("账号信息"): # 创建“账号信息”选项卡
            with gr.Row(): # 在行内布局
                with gr.Column():  # 在列内布局
                    # 创建用户ID输入框
                    userid_input = gr.Textbox(type = 'text', placeholder = "请输入账号", value=config['账号信息'].get('userid'), label = "账号", autofocus = True)
                    # 创建密码输入框
                    recv_body_input = gr.Textbox(type = 'password', placeholder = "请输入密码", value=config['账号信息'].get('password'), label = "密码")
                    # 创建登录按钮
                    submit_button = gr.Button("登录")
                with gr.Column(): # 另一列
                    # 创建用于显示登录结果或个人信息的文本框
                    result_output = gr.Textbox(label = "个人信息")
            with gr.Row():
                # 创建一个只读文本框显示资源概况的标签
                gr.Textbox(value = ("赛尔豆", "钻石", "泰坦之灵"), label = '资源概况', interactive=False) # interactive=False 使其不可编辑

        with gr.Tab("一键日常"): # 创建“一键日常”选项卡
            with gr.Tab("通用设置"): # 在“一键日常”下创建“通用设置”子选项卡
                with gr.Column():
                    with gr.Row():
                        # 创建能力装备下拉选择框
                        capability_equipment = gr.Dropdown(choices=['装备1', '装备2', '装备3'], value=config['通用设置'].get('capability_equipment'), label = "能力装备")
                        # 创建能力称号下拉选择框
                        capability_title = gr.Dropdown(choices=['称号1', '称号2', '称号3'], value=config['通用设置'].get('capability_title'), label = "能力称号")
                    with gr.Row():
                        # 创建自爆精灵下拉选择框
                        self_destructing_elf = gr.Dropdown(["帝皇之御", "幻影蝶", "仁天之君·刘备", "昭烈帝刘备", "众神之首·宙斯", "神王宙斯"], value=config['通用设置'].get('self_destructing_elf'), label = "自爆精灵")
                        # 创建弹伤精灵下拉选择框
                        rebound_damage_elf = gr.Dropdown(["六界神王", "六界帝神", "乔特鲁", "乔特鲁德", "万人敌张飞", "盖世张飞", "埃尔尼亚", "埃尔文达"], value=config['通用设置'].get('rebound_damage_elf'), label = "弹伤精灵")
                        # 创建补刀精灵下拉选择框
                        mending_blade_elf = gr.Dropdown(["圣灵谱尼", "时空界皇", "深渊狱神·哈迪斯"], value=config['通用设置'].get('mending_blade_elf'), label = "补刀精灵")

            with gr.Tab("日常设置"): # 在“一键日常”下创建“日常设置”子选项卡
                # 使用 gr.Radio 创建单选按钮组用于各项日常任务的开关
                with gr.Row():
                    daily_check_in = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('daily_check_in'), label = "日常签到")
                    a = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('a'), label = "刻印抽奖")
                    b = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('b'), label = "VIP礼包")
                    c = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('c'), label = "战队日常")
                with gr.Row():
                    d = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('d'), label = "六界神王殿")
                    e = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('e'), label = "经验战场")
                    f = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('f'), label = "学习力战场")
                    g = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('g'), label = "勇者之塔")
                with gr.Row():
                    h = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('h'), label = "泰坦矿洞")
                    i = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('i'), label = "泰坦源脉")
                    j = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('j'), label = "精灵王试炼")
                    k = gr.Radio(choices = ["默认", "84", "禁止"], value=config['日常设置'].get('k'), label = "X战队密室")
                with gr.Row():
                    l = gr.Radio(choices = ["默认", "禁止"], value=config['日常设置'].get('l'), label="星愿漂流瓶许愿")

            # 添加文本框用于显示执行日常任务的结果
            output = gr.Textbox(label="执行结果", lines=10, max_lines=20)

            with gr.Row():
                # 创建启动和结束按钮
                start_button = gr.Button(value="启动日常") # 修改按钮文本以更清晰
                # end_button = gr.Button(value="结束日常") # 结束按钮，当前未绑定功能

            # 绑定启动按钮的点击事件到 main 对象的 execute_daily_routine 方法
            start_button.click(fn=main.execute_daily_routine, inputs=[], outputs=output)

            # 结束按钮的点击事件可以绑定到 main 对象中用于停止任务的方法 (如果存在)
            # end_button.click(fn=main.stop_daily_tasks, inputs=[], outputs=output) # 假设有 stop_daily_tasks 方法

        with gr.Tab("系统设置"): # 创建“系统设置”选项卡
            with gr.Row():
                # 创建重启软件按钮
                reboot_button = gr.Button(value="重启软件")
                reboot_button.click(restart_program) # 绑定点击事件到 restart_program 函数
            with gr.Row():
                # 添加一个视频播放组件 (注意：文件路径需要有效)
                gr.Video(r"C:\Users\Admin\Downloads\1727277200922.mp4") # 示例视频路径
                # 添加一个鸣谢文本框
                gr.Textbox('''各位大佬
我自己''', label = '鸣谢', lines = 5)


        # 绑定登录按钮的点击事件到 login_action 函数
        submit_button.click(fn=login_action, inputs=[userid_input, recv_body_input], outputs=result_output)

        # 定义所有需要保存的设置输入控件列表
        settings_inputs=[userid_input, recv_body_input, capability_equipment, capability_title,
                         self_destructing_elf, rebound_damage_elf, mending_blade_elf,
                         daily_check_in, a, b, c, d, e, f, g, h, i, j, k, l]

        # 为每个设置相关的输入控件绑定 change 事件到 save_user_settings 函数
        # 当控件的值发生改变时，会自动调用 save_user_settings 函数保存所有设置
        for component in settings_inputs:
            component.change(save_user_settings, inputs=settings_inputs, outputs=None) # outputs=None 因为保存操作通常不需要直接更新UI的某个特定输出

    demo.launch(inbrowser=True) # 启动 Gradio 应用，并在浏览器中打开

if __name__ == '__main__': # 当脚本作为主程序运行时
    create_ui() # 调用 create_ui 函数创建并启动界面
