import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import datetime
import random


class TransportNetwork:
    def __init__(self):
        self.network = nx.MultiGraph()
        self.transport_types = {'Metro', 'Bus', 'Train'}
        self.schedules = defaultdict(list)
        self.station_capacity = {}

    def add_station(self, station_id, capacity, coordinates=None):
        self.network.add_node(station_id,
                              capacity=capacity,
                              coordinates=coordinates or (random.random(), random.random()))
        self.station_capacity[station_id] = capacity

    def add_connection(self, start, end, transport_type, travel_time, schedule=None):
        if transport_type not in self.transport_types:
            raise ValueError(f"Invalid transport type. Must be one of {self.transport_types}")

        # Add edge with a specific key for the transport type
        key = self.network.add_edge(start, end)
        self.network[start][end][key].update({
            'transport_type': transport_type,
            'travel_time': travel_time,
            'schedule': schedule or self._generate_schedule()
        })

    def _generate_schedule(self, start_hour=5, end_hour=23, frequency=15):
        schedule = []
        current_time = datetime.datetime.now().replace(hour=start_hour, minute=0)
        end_time = current_time.replace(hour=end_hour)

        while current_time <= end_time:
            schedule.append(current_time.strftime("%H:%M"))
            current_time += datetime.timedelta(minutes=frequency)
        return schedule

    def find_optimal_route(self, start, end, time=None, preferences=None):
        if start not in self.network or end not in self.network:
            raise ValueError("Start or end station not found in network")

        if preferences is None:
            preferences = {'Metro': 1, 'Bus': 1.5, 'Train': 1.2}

        def weight_function(u, v, attrs):
            min_weight = float('inf')
            for k in self.network[u][v]:
                edge_data = self.network[u][v][k]
                if 'transport_type' in edge_data and 'travel_time' in edge_data:
                    transport_type = edge_data['transport_type']
                    weight = edge_data['travel_time'] * preferences.get(transport_type, 1)
                    min_weight = min(min_weight, weight)
            return min_weight if min_weight != float('inf') else 1

        try:
            path = nx.shortest_path(self.network, start, end, weight=weight_function)
            total_time = self._calculate_total_time(path)
            transfers = self._count_transfers(path)
            return path, total_time, transfers
        except nx.NetworkXNoPath:
            raise ValueError(f"No path found between {start} and {end}")

    def _count_transfers(self, path):
        transfers = 0
        for i in range(len(path) - 2):
            current_transport = None
            next_transport = None

            # Get transport type for current segment
            for k in self.network[path[i]][path[i + 1]]:
                current_transport = self.network[path[i]][path[i + 1]][k].get('transport_type')
                if current_transport:
                    break

            # Get transport type for next segment
            for k in self.network[path[i + 1]][path[i + 2]]:
                next_transport = self.network[path[i + 1]][path[i + 2]][k].get('transport_type')
                if next_transport:
                    break

            if current_transport and next_transport and current_transport != next_transport:
                transfers += 1

        return transfers

    def _calculate_total_time(self, path):
        total_time = 0
        for i in range(len(path) - 1):
            min_time = float('inf')
            for k in self.network[path[i]][path[i + 1]]:
                edge_data = self.network[path[i]][path[i + 1]][k]
                if 'travel_time' in edge_data:
                    min_time = min(min_time, edge_data['travel_time'])
            total_time += min_time if min_time != float('inf') else 0
        return total_time

    def visualize_network(self, highlight_path=None):
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.network)

        # Draw different transport types in different colors
        colors = {'Metro': 'red', 'Bus': 'blue', 'Train': 'green'}

        # Draw edges for each transport type
        for transport_type in self.transport_types:
            edge_list = []
            for u, v, k, data in self.network.edges(data=True, keys=True):
                if data.get('transport_type') == transport_type:
                    edge_list.append((u, v))
            if edge_list:
                nx.draw_networkx_edges(self.network, pos, edgelist=edge_list,
                                       edge_color=colors[transport_type],
                                       label=transport_type)

        # Draw stations
        nx.draw_networkx_nodes(self.network, pos, node_color='lightgray',
                               node_size=[self.station_capacity[node] * 100
                                          for node in self.network.nodes()])
        nx.draw_networkx_labels(self.network, pos)

        # Highlight path if provided
        if highlight_path:
            path_edges = list(zip(highlight_path[:-1], highlight_path[1:]))
            nx.draw_networkx_edges(self.network, pos, edgelist=path_edges,
                                   edge_color='yellow', width=2)

        plt.title("Public Transportation Network")
        plt.legend()
        plt.axis('off')
        plt.show()


def create_sample_network():
    network = TransportNetwork()

    # Add stations with different capacities
    stations = {
        'Ramsis_square': 1000,
        'North': 500,
        'South': 500,
        'East': 300,
        'West': 300,
        'Airport': 800
    }

    for station, capacity in stations.items():
        network.add_station(station, capacity)

    # Add connections with different transport types
    connections = [
        ('Ramsis_square', 'North', 'Metro', 21),
        ('Ramsis_square', 'South', 'Metro', 20),
        ('Ramsis_square', 'Airport', 'Train', 24),
        ('North', 'East', 'Bus', 30),
        ('South', 'West', 'Bus', 25),
        ('East', 'Airport', 'Bus', 30),
        ('West', 'Airport', 'Train', 25)
    ]

    for start, end, transport_type, time in connections:
        network.add_connection(start, end, transport_type, time)

    return network


# Test the implementation
if __name__ == "__main__":
    network = create_sample_network()

    try:
        # Test route finding
        start, end = 'West', 'Airport'
        path, time, transfers = network.find_optimal_route(start, end)
        print(f"\nRoute from {start} to {end}:")
        print(f"Path: {' -> '.join(path)}")
        print(f"Total time: {time} minutes")
        print(f"Number of transfers: {transfers}")

        # Visualize the network
        network.visualize_network(highlight_path=path)

    except Exception as e:
        print(f"Error: {e}")
network = create_sample_network()

try:
    # Find a route
    path, time, transfers = network.find_optimal_route('Ramsis_square', 'Airport')
    print(f"Route: {' -> '.join(path)}")
    print(f"Time: {time} minutes")
    print(f"Transfers: {transfers}")

    # Show the network
    network.visualize_network(highlight_path=path)
except Exception as e:
    print(f"Error: {e}")