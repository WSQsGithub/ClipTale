import cProfile

from gui.splash_screen import start_app

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    start_app()
    profiler.disable()  # 结束 profiling

    # 打印结果
    profiler.print_stats(sort="cumulative")  # 按累计时间排序
