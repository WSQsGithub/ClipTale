import cProfile
from functools import wraps


def profile(output_file="profile.prof"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            try:
                return profiler.runcall(func, *args, **kwargs)
            finally:
                profiler.dump_stats(output_file)
                print(f"Profiling results saved to {output_file}")
                print(f"Use 'snakeviz {output_file}' to visualize.")

        return wrapper

    return decorator


# Example usage
def main():
    @profile("example.prof")
    def example_function(x):
        total = 0
        for i in range(x):
            total += i
        return total

    result = example_function(1000000)
    print(result)


if __name__ == "__main__":
    main()
