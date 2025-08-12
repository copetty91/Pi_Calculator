import math
import os
import time
import json
import socket
import platform
from decimal import Decimal, getcontext


def get_system_info():
    """Get system information for benchmarking."""
    try:
        hostname = socket.gethostname()
        system_info = {
            'hostname': hostname,
            'system': platform.system(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'python_version': platform.python_version()
        }
        return system_info
    except Exception as e:
        return {'hostname': 'unknown', 'error': str(e)}


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
    system_info = get_system_info()
    hostname = system_info['hostname']
    filename = f'pi_benchmarks_{hostname}.json'

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            return data, filename
    except FileNotFoundError:
        return {'system_info': system_info, 'benchmarks': {}}, filename


def save_benchmark_data(benchmark_data, filename):
    """Save benchmark data to file."""
    with open(filename, 'w') as f:
        json.dump(benchmark_data, f, indent=2)


def load_all_benchmark_files():
    """Load all benchmark files in the current directory for comparison."""
    all_benchmarks = {}

    # Look for all pi_benchmarks_*.json files
    for file in os.listdir('.'):
        if file.startswith('pi_benchmarks_') and file.endswith('.json'):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    hostname = data.get('system_info', {}).get('hostname', 'unknown')
                    all_benchmarks[hostname] = data
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")

    return all_benchmarks


def estimate_time_from_benchmarks(digits, benchmarks):
    """Estimate calculation time based on previous benchmarks."""
    if len(benchmarks) < 2:
        return None

    digit_counts = [int(d) for d in benchmarks.keys()]
    times = [benchmarks[str(d)] for d in digit_counts]

    if len(digit_counts) < 2:
        return None

    digit_counts.sort()
    times_sorted = [benchmarks[str(d)] for d in digit_counts]

    if digits <= max(digit_counts):
        for i in range(len(digit_counts) - 1):
            if digit_counts[i] <= digits <= digit_counts[i + 1]:
                d1, d2 = digit_counts[i], digit_counts[i + 1]
                t1, t2 = times_sorted[i], times_sorted[i + 1]
                if d1 > 0 and d2 > 0 and t1 > 0 and t2 > 0:
                    power = math.log(t2 / t1) / math.log(d2 / d1)
                    estimated = t1 * (digits / d1) ** power
                    return estimated
    else:
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


def save_pi_to_file(pi_value, digits, folder_path, calculation_time, system_info):
    """Save the calculated pi value to a text file."""
    file_start_time = time.time()

    os.makedirs(folder_path, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    hostname = system_info.get('hostname', 'unknown')
    filename = f"pi_{digits}_digits_{hostname}_{timestamp}.txt"
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
        file.write(f"System: {hostname}\n")
        file.write(f"Platform: {system_info.get('system', 'Unknown')} {system_info.get('machine', '')}\n")
        file.write(f"Processor: {system_info.get('processor', 'Unknown')}\n")
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


def show_comparison_table(all_benchmarks):
    """Display a comparison table of all systems."""
    if len(all_benchmarks) < 2:
        return

    print("\n" + "=" * 80)
    print("🏆 MULTI-SYSTEM PERFORMANCE COMPARISON")
    print("=" * 80)

    # Get all unique digit counts across all systems
    all_digits = set()
    for hostname, data in all_benchmarks.items():
        benchmarks = data.get('benchmarks', {})
        all_digits.update(int(d) for d in benchmarks.keys())

    if not all_digits:
        print("No benchmark data found across systems.")
        return

    all_digits = sorted(all_digits)

    # Table header
    print(f"{'System':<20} {'Platform':<15}", end='')
    for digits in all_digits:
        print(f"{digits:>12} digits", end='')
    print(f"{'Rate (d/s)':<12}")
    print("-" * 80)

    # System rows
    for hostname, data in sorted(all_benchmarks.items()):
        system_info = data.get('system_info', {})
        benchmarks = data.get('benchmarks', {})
        platform_info = f"{system_info.get('system', 'Unknown')}"

        print(f"{hostname:<20} {platform_info:<15}", end='')

        # Show times for each digit count
        times_for_rate = []
        digits_for_rate = []

        for digits in all_digits:
            if str(digits) in benchmarks:
                time_taken = benchmarks[str(digits)]
                print(f"{format_time(time_taken):>18}", end='')
                times_for_rate.append(time_taken)
                digits_for_rate.append(digits)
            else:
                print(f"{'--':>18}", end='')

        # Calculate average rate
        if times_for_rate and digits_for_rate:
            avg_rate = sum(d / t for d, t in zip(digits_for_rate, times_for_rate)) / len(times_for_rate)
            print(f"{avg_rate:>10.0f}")
        else:
            print(f"{'--':>12}")

    print("\n🥇 Performance Rankings:")

    # Find the best system for each digit count
    for digits in all_digits:
        fastest_time = float('inf')
        fastest_system = None

        for hostname, data in all_benchmarks.items():
            benchmarks = data.get('benchmarks', {})
            if str(digits) in benchmarks:
                time_taken = benchmarks[str(digits)]
                if time_taken < fastest_time:
                    fastest_time = time_taken
                    fastest_system = hostname

        if fastest_system:
            rate = digits / fastest_time
            print(f"   {digits:>5} digits: 🥇 {fastest_system:<20} ({format_time(fastest_time)}, {rate:,.0f} d/s)")


def benchmark_mode():
    """Run benchmark mode to collect performance data."""
    system_info = get_system_info()
    hostname = system_info['hostname']

    print(f"\n🏃‍♂️ Benchmark Mode - System: {hostname}")
    print("=" * 50)
    print("This will run a few quick calculations to calibrate time estimates for your system.")

    benchmark_tests = [100, 500, 1000]
    benchmark_data, filename = load_benchmark_data()
    benchmarks = benchmark_data['benchmarks']

    print(f"\n💻 System Info:")
    print(f"   Hostname: {system_info.get('hostname', 'Unknown')}")
    print(f"   Platform: {system_info.get('system', 'Unknown')} {system_info.get('machine', '')}")
    print(f"   Processor: {system_info.get('processor', 'Unknown')}")

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

    # Update the benchmark data with current system info
    benchmark_data['system_info'] = system_info
    benchmark_data['benchmarks'] = benchmarks
    benchmark_data['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')

    save_benchmark_data(benchmark_data, filename)
    print(f"\n📊 Benchmark data saved to: {filename}")
    print(f"Your {hostname} performance profile:")

    for digits in sorted([int(d) for d in benchmarks.keys()]):
        time_taken = benchmarks[str(digits)]
        rate = digits / time_taken if time_taken > 0 else 0
        print(f"   {digits:5} digits: {format_time(time_taken):>15} ({rate:,.0f} digits/sec)")

    return benchmark_data['benchmarks']


def main():
    """Main function to run the pi calculator with user input."""
    system_info = get_system_info()
    hostname = system_info['hostname']

    print("🥧 Pi Calculator using Chudnovsky Algorithm 🥧")
    print("=" * 50)
    print(f"💻 Running on: {hostname}")

    # Load current system's benchmarks
    benchmark_data, filename = load_benchmark_data()
    benchmarks = benchmark_data['benchmarks']

    # Load all benchmark files for comparison
    all_benchmarks = load_all_benchmark_files()

    if not benchmarks:
        print(f"\n🎯 First time running on {hostname}? Let's benchmark this system!")
        run_bench = input("Run quick benchmark? (recommended - y/n): ").lower()
        if run_bench == 'y':
            benchmarks = benchmark_mode()
    else:
        print(f"\n📊 Found benchmark data for {hostname}:")
        for digits in sorted([int(d) for d in benchmarks.keys()]):
            time_taken = benchmarks[str(digits)]
            print(f"   {digits} digits: {format_time(time_taken)}")

        # Show comparison if other systems exist
        if len(all_benchmarks) > 1:
            show_comp = input("\nShow multi-system comparison? (y/n): ").lower()
            if show_comp == 'y':
                show_comparison_table(all_benchmarks)

        update_bench = input(f"\nUpdate benchmark data for {hostname}? (y/n): ").lower()
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
                    print(f"⏱️  Estimated time for {hostname}: {format_time(estimated_time)}")
                    if estimated_time > 300:  # 5 minutes
                        print("🚨 This calculation may take a long time!")
                        confirm = input("Continue? (y/n): ").lower()
                        if confirm != 'y':
                            continue
                else:
                    print(f"⚠️  No benchmark data available for {hostname} estimation")

                break
            except ValueError:
                print("Please enter a valid integer.")

        # Get folder path
        folder_path = input("\nEnter folder path (or press Enter for current directory): ").strip()
        if not folder_path:
            folder_path = "."

        print(f"\n🔢 Starting calculation of pi to {digits} decimal places on {hostname}...")
        print("⏱️  Timer started!")

        # Calculate pi
        pi_result, calc_time = chudnovsky_pi(digits)

        # Save this result as benchmark data
        benchmarks[str(digits)] = calc_time
        benchmark_data['benchmarks'] = benchmarks
        benchmark_data['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
        save_benchmark_data(benchmark_data, filename)

        print(f"\n✅ Calculation complete!")
        print(f"⏱️  Calculation time: {format_time(calc_time)}")

        if estimated_time:
            accuracy = (calc_time / estimated_time) if estimated_time > 0 else 0
            print(f"🎯 Estimate accuracy: {accuracy:.1f}x (1.0x = perfect)")

        # Save to file
        file_path, file_time = save_pi_to_file(pi_result, digits, folder_path, calc_time, system_info)

        total_time = time.time() - overall_start_time
        print(f"\n📈 Timing Summary for {hostname}:")
        print(f"   Calculation: {format_time(calc_time)}")
        print(f"   File Save:   {format_time(file_time)}")
        print(f"   Total Time:  {format_time(total_time)}")

        if calc_time > 0:
            digits_per_second = digits / calc_time
            print(f"   Performance: {digits_per_second:,.2f} digits/second")

        print(f"📁 Result saved to: {file_path}")

        # Show preview
        pi_str = str(pi_result)
        preview = pi_str[:47] + "..." if len(pi_str) > 50 else pi_str
        print(f"\n🔍 Preview: {preview}")

    except KeyboardInterrupt:
        print("\n\n❌ Calculation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

    print(f"\nThank you for using the Pi Calculator on {hostname}! 🎉")


if __name__ == "__main__":
    main()
