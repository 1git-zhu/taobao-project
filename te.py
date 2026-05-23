# 基础关键词分类
styles = ["北欧风格", "现代简约", "新中式", "日式风格", "美式乡村", "欧式奢华"]
rooms = ["客厅", "卧室", "厨房", "卫生间", "阳台", "书房"]
materials = ["地板", "瓷砖", "壁纸", "墙漆", "吊顶", "灯具"]
furniture = ["沙发", "床", "餐桌椅", "衣柜", "电视柜", "茶几"]
accessories = ["窗帘", "地毯", "抱枕", "收纳柜", "装饰画", "花瓶"]
functions = ["智能家居", "节能灯", "防潮收纳", "儿童家具", "老人家具", "室内绿植"]

# 存放所有关键词的集合（去重）
keywords_set = set()

# 1. 所有单个关键词
for lst in [styles, rooms, materials, furniture, accessories, functions]:
    keywords_set.update(lst)

print(list(keywords_set))
