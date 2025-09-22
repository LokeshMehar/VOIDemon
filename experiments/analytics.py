    failure_rates = [row[0] for row in data]
    success_rates = [row[1] for row in data]

    plt.figure(figsize=(10, 6))
    plt.plot(failure_rates, success_rates, marker='o', color='b')
    plt.xlabel('Failure Rate (%)')
    plt.ylabel('Query Success Rate')
    plt.title('VOIDemon: Query Success vs Node Failure Rate')
    plt.grid(True)
    plt.savefig('query_success_vs_failure_rate.png')
    print("Saved query_success_vs_failure_rate.png")


def plot_bandwidth_savings_over_time(analytics_db):
    data = analytics_db.get_bandwidth_savings_over_time()
    if not data:
        print("No data for Bandwidth Savings Over Time.")
        return

    rounds = [row[0] for row in data]
    sent = [row[1] for row in data]
    filtered = [row[2] for row in data]

    plt.figure(figsize=(10, 6))
    plt.plot(rounds, sent, label='Metrics Sent (Bandwidth Used)', color='red', marker='o')
    plt.plot(rounds, filtered, label='Metrics Filtered by VoI (Saved)', color='green', marker='x')
    plt.xlabel('Gossip Round')
    plt.ylabel('Number of Metrics')
    plt.title('VOIDemon: Metric Transmission Over Time (VoI Bandwidth Savings)')
