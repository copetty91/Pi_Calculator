import math
import os
import time
import json
from decimal import Decimal, getcontext


def format_time(seconds):
    """Format time in a human-readable way."""
    if seconds < 1:
        return f"{seconds * 1000:.2f} milliseconds"
    elif seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes} minute(s) and {remaining_seconds:.2f} seconds"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours} hour(s), {remaining_minutes} minute(s) and {remaining_seconds:.2f} seconds"


def load_benchmark_data():
    """Load benchmark data from file if it exists."""
    try:
        with open('pi_benchmarks.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_benchmark_data(benchmarks):
    """Save benchmark data to file."""
    with open('pi_benchmarks.json', 'w') as f:
        json.dump(benchmarks, f, indent=2)


def estimate_time_from_benchmarks(digits, benchmarks):
    """
    Estimate calculation time based on previous benchmarks.
    Uses power law fitting: time = a * digits^b
    """
    if len(benchmarks) < 2:
        return None

    # Convert to lists for easier handling
    digit_counts = [int(d) for d in benchmarks.keys()]
    times = [benchmarks[str(d)] for d in digit_counts]

    if len(digit_counts) < 2:
        return None

    # Simple power law estimation using two points
    # If we have more points, we could do a proper curve fit
    digit_counts.sort()
    times_sorted = [benchmarks[str(d)] for d in digit_counts]

    # Use the two most recent/relevant data points
    if digits <= max(digit_counts):
        # Interpolation case - find closest points
        for i in range(len(digit_counts) - 1):
            if digit_counts[i] <= digits <= digit_counts[i + 1]:
                d1, d2 = digit_counts[i], digit_counts[i + 1]
                t1, t2 = times_sorted[i], times_sorted[i + 1]
                # Power law interpolation
                if d1 > 0 and d2 > 0 and t1 > 0 and t2 > 0:
                    power = math.log(t2 / t1) / math.log(d2 / d1)
                    estimated = t1 * (digits / d1) ** power
                    return estimated
    else:
        # Extrapolation case - use the two highest data points
        if len(digit_counts) >= 2:
            d1, d2 = digit_counts[-2], digit_counts[-1]
            t1, t2 = times_sorted[-2], times_sorted[-1]
            if d1 > 0 and d2 > 0 and t1 > 0 and t2 > 0:
                power = math.log(t2 / t1) / math.log(d2 / d1)
                estimated = t2 * (digits / d2) ** power
                return estimated

    return None


def chudnovsky_pi(precision):
    """Calculate pi using the Chudnovsky algorithm."""
    start_time = time.time()

    getcontext().prec = precision + 100

    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L

    iterations = int(precision / 14.18) + 10

    print(f"🔄 Running {iterations} iterations...")

    progress_interval = max(1, iterations // 20)

    for i in range(1, iterations):
        if i % progress_interval == 0 and iterations > 50:
            progress = (i / iterations) * 100
            elapsed = time.time() - start_time
            print(f"   Progress: {progress:.1f}% - Elapsed: {format_time(elapsed)}")

        M = (K * (K - 1) * (K - 2) * (K - 3) * (K - 4) * (K - 5) * M) // (i ** 3)
        K += 6
        L += 545140134
        X *= -262537412640768000
        S += Decimal(M * L) / X

    pi_value = C / S
    getcontext().prec = precision + 10
    calculation_time = time.time() - start_time

    return +pi_value, calculation_time


def save_pi_to_file(pi_value, digits, folder_path, calculation_time):
    """Save the calculated pi value to a text file."""
    file_start_time = time.time()

    os.makedirs(folder_path, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"pi_{digits}_digits_{timestamp}.txt"
    file_path = os.path.join(folder_path, filename)

    pi_str = str(pi_value)

    if '.' in pi_str:
        integer_part, decimal_part = pi_str.split('.')
        if len(decimal_part) > digits:
            decimal_part = decimal_part[:digits]
        pi_formatted = f"{integer_part}.{decimal_part}"
    else:
        pi_formatted = pi_str

    with open(file_path, 'w') as file:
        file.write(f"Pi Calculator - Chudnovsky Algorithm Results\n")
        file.write("=" * 50 + "\n\n")
        file.write(f"Calculation Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"Requested Precision: {digits} decimal places\n")
        file.write(f"Calculation Time: {format_time(calculation_time)}\n")
        file.write(f"Algorithm: Chudnovsky Algorithm\n\n")
        file.write("Pi Value:\n")
        file.write("-" * 20 + "\n")
        file.write(pi_formatted)
        file.write(f"\n\n")
        file.write("Summary:\n")
        file.write("-" * 20 + "\n")
        file.write(f"Total digits after decimal point: {len(decimal_part) if '.' in pi_formatted else 0}\n")
        file.write(f"Calculation completed successfully in {format_time(calculation_time)}!\n")

    file_time = time.time() - file_start_time
    return file_path, file_time


def benchmark_mode():
    """Run benchmark mode to collect performance data."""
    print("\n🏃‍♂️ Benchmark Mode")
    print("=" * 30)
    print("This will run a few quick calculations to calibrate time estimates for your system.")

    benchmark_tests = [100, 500, 1000]
    benchmarks = load_benchmark_data()

    for digits in benchmark_tests:
        if str(digits) in benchmarks:
            print(f"✅ {digits} digits: {format_time(benchmarks[str(digits)])} (cached)")
            continue

        print(f"\n🔢 Testing {digits} digits...")
        try:
            pi_result, calc_time = chudnovsky_pi(digits)
            benchmarks[str(digits)] = calc_time
            print(f"✅ Completed in {format_time(calc_time)}")
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    save_benchmark_data(benchmarks)
    print(f"\n📊 Benchmark data saved! Your system profile:")
    for digits in sorted([int(d) for d in benchmarks.keys()]):
        time_taken = benchmarks[str(digits)]
        rate = digits / time_taken if time_taken > 0 else 0
        print(f"   {digits:5} digits: {format_time(time_taken):>15} ({rate:,.0f} digits/sec)")

    return benchmarks


def main():
    """Main function to run the pi calculator with user input."""
    print("🥧 Pi Calculator using Chudnovsky Algorithm 🥧")
    print("=" * 50)

    # Load existing benchmarks
    benchmarks = load_benchmark_data()

    if not benchmarks:
        print("\n🎯 First time running? Let's benchmark your system!")
        run_bench = input("Run quick benchmark? (recommended - y/n): ").lower()
        if run_bench == 'y':
            benchmarks = benchmark_mode()
    else:
        print(f"\n📊 Found benchmark data from previous runs:")
        for digits in sorted([int(d) for d in benchmarks.keys()]):
            time_taken = benchmarks[str(digits)]
            print(f"   {digits} digits: {format_time(time_taken)}")

        update_bench = input("\nUpdate benchmark data? (y/n): ").lower()
        if update_bench == 'y':
            benchmarks = benchmark_mode()

    overall_start_time = time.time()

    try:
        while True:
            try:
                digits = int(input("\nEnter the number of decimal places to calculate: "))
                if digits < 1:
                    print("Please enter a positive number.")
                    continue

                # Show estimate based on benchmarks
                estimated_time = estimate_time_from_benchmarks(digits, benchmarks)
                if estimated_time:
                    print(f"⏱️  Estimated time based on your system: {format_time(estimated_time)}")
                    if estimated_time > 300:  # 5 minutes
                        print("🚨 This calculation may take a long time!")
                        confirm = input("Continue? (y/n): ").lower()
                        if confirm != 'y':
                            continue
                else:
                    print("⚠️  No benchmark data available for estimation")

                break
            except ValueError:
                print("Please enter a valid integer.")

        # Get folder path
        folder_path = input("\nEnter folder path (or press Enter for current directory): ").strip()
        if not folder_path:
            folder_path = "."

        print(f"\n🔢 Starting calculation of pi to {digits} decimal places...")
        print("⏱️  Timer started!")

        # Calculate pi
        pi_result, calc_time = chudnovsky_pi(digits)

        # Save this result as benchmark data
        benchmarks[str(digits)] = calc_time
        save_benchmark_data(benchmarks)

        print(f"\n✅ Calculation complete!")
        print(f"⏱️  Calculation time: {format_time(calc_time)}")

        if estimated_time:
            accuracy = (calc_time / estimated_time) if estimated_time > 0 else 0
            print(f"🎯 Estimate accuracy: {accuracy:.1f}x (1.0x = perfect)")

        # Save to file
        file_path, file_time = save_pi_to_file(pi_result, digits, folder_path, calc_time)

        total_time = time.time() - overall_start_time
        print(f"\n📈 Timing Summary:")
        print(f"   Calculation: {format_time(calc_time)}")
        print(f"   File Save:   {format_time(file_time)}")
        print(f"   Total Time:  {format_time(total_time)}")

        if calc_time > 0:
            digits_per_second = digits / calc_time
            print(f"   Performance: {digits_per_second:,.2f} digits/second")

        # Show preview
        pi_str = str(pi_result)
        preview = pi_str[:47] + "..." if len(pi_str) > 50 else pi_str
        print(f"\n🔍 Preview: {preview}")

    except KeyboardInterrupt:
        print("\n\n❌ Calculation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

    print("\nThank you for using the Pi Calculator! 🎉")


if __name__ == "__main__":
    main()
