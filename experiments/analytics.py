"""
analytics.py — VOIDemon Post-Run Analytics

Generates PNG charts from the VOIDemon experiment database after a run completes.
Charts produced:
  - Query success rate vs node failure rate
  - Metric bandwidth savings over gossip rounds
  - Total metric transmission pie chart (sent vs filtered by VoI)
  - Sent vs filtered breakdown by metric type (cpu / memory / network / storage)

Usage:
    python experiments/analytics.py
"""

import sqlite3
import matplotlib.pyplot as plt
import os

DB_FILE = 'voidemon.db'


class VoidemonAnalyticsDB:
    """Read-only database accessor for post-run analytics queries."""

    def __init__(self):
        db_path = DB_FILE
        if not os.path.exists(db_path):
            db_path = os.path.join(os.path.dirname(__file__), DB_FILE)
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def get_query_success_by_failure_rate(self):
        try:
            self.cursor.execute(
                "SELECT failure_percent, "
                "AVG(CASE WHEN success = 'True' OR success = '1' THEN 1 ELSE 0 END) "
                "FROM query GROUP BY failure_percent"
            )
            return self.cursor.fetchall()
        except Exception as e:
            print("Error (get_query_success_by_failure_rate): {}".format(e))
            return []

    def get_bandwidth_savings_over_time(self):
        try:
            self.cursor.execute(
                "SELECT round, SUM(metrics_sent), SUM(metrics_filtered) "
                "FROM round_metrics_stats "
                "GROUP BY round "
                "ORDER BY round"
            )
            return self.cursor.fetchall()
        except Exception as e:
            print("Error (get_bandwidth_savings_over_time): {}".format(e))
            return []

    def get_total_bandwidth_saved(self):
        try:
            self.cursor.execute(
                "SELECT SUM(metrics_sent), SUM(metrics_filtered) "
                "FROM round_metrics_stats"
            )
            return self.cursor.fetchone()
        except Exception as e:
            print("Error (get_total_bandwidth_saved): {}".format(e))
            return (0, 0)

    def get_transmissions_by_metric_type(self):
        try:
            self.cursor.execute(
                "SELECT metric_type, "
                "SUM(CASE WHEN was_sent = 1 THEN 1 ELSE 0 END) as sent, "
                "SUM(CASE WHEN was_sent = 0 THEN 1 ELSE 0 END) as filtered "
                "FROM metric_transmissions "
                "GROUP BY metric_type"
            )
            return self.cursor.fetchall()
        except Exception as e:
            print("Error (get_transmissions_by_metric_type): {}".format(e))
            return []


def plot_query_success_vs_failure_rate(analytics_db):
    data = analytics_db.get_query_success_by_failure_rate()
    if not data:
        print("No data for Query Success vs Failure Rate.")
        return
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
    plt.legend()
    plt.grid(True)
    plt.savefig('bandwidth_savings_over_time.png')
    print("Saved bandwidth_savings_over_time.png")


def plot_total_bandwidth_saved(analytics_db):
    data = analytics_db.get_total_bandwidth_saved()
    if not data or data == (None, None) or (data[0] == 0 and data[1] == 0):
        print("No data for Total Bandwidth Saved Pie Chart.")
        return

    sent, filtered = data
    labels = ['Metrics Transmitted', 'Metrics Filtered (VoI Saved)']
    sizes = [sent, filtered]
    colors = ['#ff9999', '#66b3ff']

    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('VOIDemon: Total VoI Bandwidth Savings')
    plt.axis('equal')
    plt.savefig('total_bandwidth_saved.png')
    print("Saved total_bandwidth_saved.png")


def plot_transmissions_by_metric_type(analytics_db):
    data = analytics_db.get_transmissions_by_metric_type()
    if not data:
        print("No data for Transmissions By Metric Type.")
        return

    metrics = [row[0] for row in data]
    sent = [row[1] for row in data]
    filtered = [row[2] for row in data]

    x = range(len(metrics))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar(x, sent, width, label='Transmitted', color='salmon')
    plt.bar([i + width for i in x], filtered, width, label='Filtered by VoI (Saved)', color='lightgreen')
    plt.xlabel('Metric Type')
    plt.ylabel('Count')
    plt.title('VOIDemon: Transmission vs VoI Filtering by Metric Type')
    plt.xticks([i + width / 2 for i in x], metrics)
    plt.legend()
    plt.grid(axis='y')
    plt.savefig('transmissions_by_metric_type.png')
    print("Saved transmissions_by_metric_type.png")


if __name__ == '__main__':
    analytics_db = VoidemonAnalyticsDB()

    plot_query_success_vs_failure_rate(analytics_db)
    plot_bandwidth_savings_over_time(analytics_db)
    plot_total_bandwidth_saved(analytics_db)
    plot_transmissions_by_metric_type(analytics_db)

    print("All analytics charts generated.")
