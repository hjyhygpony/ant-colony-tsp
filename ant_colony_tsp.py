import numpy as np
import matplotlib.pyplot as plt
import math
import random

np.random.seed(42)
random.seed(42)

# 设置中文字体，防止画图乱码
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 1. 初始化城市名称以及坐标
def init_map():
    city_name = []
    city_xy = []
    try:
        with open('data.txt', 'r', encoding='UTF-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                parts = line.split(',')
                city_name.append(parts[0])
                city_xy.append([float(parts[1]), float(parts[2])])
    except FileNotFoundError:
        print("错误：未找到 data.txt 文件，请确保文件在同级目录下。")
        exit()
    return city_name, np.array(city_xy)


# 2. 计算距离矩阵
def init_d(city_name, city_xy):
    city_count = len(city_name)
    Distance = np.zeros((city_count, city_count))
    for i in range(city_count):
        for j in range(city_count):
            if i != j:
                Distance[i][j] = math.sqrt((city_xy[i][0] - city_xy[j][0]) ** 2 + (city_xy[i][1] - city_xy[j][1]) ** 2)
            else:
                Distance[i][j] = 10000  # 也就是无穷大
    return Distance  # 必须返回计算好的矩阵


# 3. 蚁群算法核心逻辑
def ACO(AntCount, city_count, alpha, beta, rho, MAX_iter, Q, pheromonetable, Distance, etable):
    # 存放每次迭代的最优距离
    distance_best = np.zeros(MAX_iter)
    # 存放每次迭代的最优路径
    path_best = np.zeros((MAX_iter, city_count))

    iter = 0
    while iter < MAX_iter:
        # candidate 存放蚂蚁的路径：行是蚂蚁，列是访问的城市顺序
        candidate = np.zeros((AntCount, city_count)).astype(int)

        # --- ① 蚂蚁初始点选择 ---
        # 随机分配蚂蚁到各个城市
        for i in range(AntCount):
            candidate[i, 0] = np.random.randint(0, city_count)

        length = np.zeros(AntCount)  # 记录每只蚂蚁的当前路径长度

        # --- ② 为每只蚂蚁构造路径 ---
        for i in range(AntCount):
            unvisit = list(range(city_count))  # 未访问城市列表
            visit = candidate[i, 0]  # 当前所在城市
            unvisit.remove(visit)

            for j in range(1, city_count):  # 访问剩下的城市
                protrans = np.zeros(len(unvisit))

                # 计算转移概率
                for k in range(len(unvisit)):
                    # 核心公式：P = (信息素^alpha) * (启发因子^beta)
                    # 启发因子通常是 1/距离
                    protrans[k] = np.power(pheromonetable[visit][unvisit[k]], alpha) * \
                                  np.power(etable[visit][unvisit[k]], beta)

                # 轮盘赌选择下一个城市
                if sum(protrans) == 0:  # 防止除零错误
                    k_index = np.random.randint(len(unvisit))
                else:
                    cumsumprobtrans = (protrans / sum(protrans)).cumsum()
                    cumsumprobtrans -= np.random.rand()
                    k_index = list(cumsumprobtrans > 0).index(True)

                next_city = unvisit[k_index]
                candidate[i, j] = next_city
                length[i] += Distance[visit][next_city]

                unvisit.remove(next_city)
                visit = next_city

            # 回到起点
            length[i] += Distance[visit][candidate[i, 0]]

        # --- ③ 更新最优解 ---
        if iter == 0:
            distance_best[iter] = length.min()
            path_best[iter] = candidate[length.argmin()].copy()
        else:
            if length.min() < distance_best[iter - 1]:  # 找到了更好的解
                distance_best[iter] = length.min()
                path_best[iter] = candidate[length.argmin()].copy()
            else:  # 没有更好，保持上一次的最优
                distance_best[iter] = distance_best[iter - 1]
                path_best[iter] = path_best[iter - 1].copy()

        # --- ④ 更新信息素 ---
        changepheromonetable = np.zeros((city_count, city_count))
        for i in range(AntCount):
            for j in range(city_count - 1):
                # 蚂蚁走过的路径增加信息素，增加量 = Q / 路径总长
                changepheromonetable[candidate[i, j]][candidate[i, j + 1]] += Q / length[i]
            # 最后一段路（回到起点）
            changepheromonetable[candidate[i, city_count - 1]][candidate[i, 0]] += Q / length[i]

        # 信息素挥发 + 新增
        pheromonetable = (1 - rho) * pheromonetable + changepheromonetable

        # 打印进度
        if iter % 10 == 0:
            print(f"迭代次数: {iter}, 当前最短距离: {distance_best[iter]:.2f}")

        iter += 1

    return path_best, distance_best


# 4. 绘图结果
def draw(path_best, city_xy, distance_best, city_name):
    best_path = path_best[-1].astype(int)
    print("-----------------------------------------")
    print(f"蚁群算法最终最优路径距离: {distance_best[-1]:.2f}")

    # 打印路径名称
    route_str = " -> ".join([city_name[i] for i in best_path])
    print(f"路径: {route_str} -> {city_name[best_path[0]]}")

    # 图1：路线轨迹图
    fig1 = plt.figure(figsize=(10, 6))
    plt.title("最佳旅行路线图 (Best Roadmap)")
    x = []
    y = []
    for i in range(len(best_path)):
        city_idx = best_path[i]
        x.append(city_xy[city_idx][0])
        y.append(city_xy[city_idx][1])
        # 标注城市名
        plt.text(city_xy[city_idx][0], city_xy[city_idx][1], city_name[city_idx], fontsize=9, color='blue')

    # 闭环
    x.append(x[0])
    y.append(y[0])

    plt.plot(x, y, '-o', color='red', linewidth=1.5)
    plt.xlabel("经度")
    plt.ylabel("纬度")
    plt.grid(True, linestyle='--', alpha=0.5)

    # 图2：算法收敛曲线
    fig2 = plt.figure(figsize=(10, 6))
    plt.title("算法收敛曲线 (Distance Iteration Graph)")
    plt.plot(range(1, len(distance_best) + 1), distance_best, color='green')
    plt.xlabel("迭代次数 (Iterations)")
    plt.ylabel("最短路径距离 (Distance)")
    plt.grid(True)

    plt.show()


if __name__ == '__main__':
    # 1. 读数据
    city_name, city_xy = init_map()

    # 2. 计算距离矩阵
    Distance = init_d(city_name, city_xy)

    # 3. 设置参数 (这些可以写进报告的参数设置部分)
    AntCount = 50  # 蚂蚁数量
    city_count = len(city_name)
    alpha = 1  # 信息素重要程度
    beta = 5  # 启发式因子(距离)重要程度
    rho = 0.001  # 信息素挥发速度
    Q = 1  # 信息素常数
    MAX_iter = 100  # 最大迭代次数

    # 初始化信息素和启发信息
    pheromonetable = np.ones((city_count, city_count))
    etable = 1.0 / Distance

    # 4. 运行算法
    print("开始运行蚁群算法...")
    path_best, distance_best = ACO(AntCount, city_count, alpha, beta, rho, MAX_iter, Q, pheromonetable, Distance,
                                   etable)

    # 5. 画图
    draw(path_best, city_xy, distance_best, city_name)
