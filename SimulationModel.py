import queue
import numpy as np


class DemandNumberTimeInterval:
    def __init__(self):
        self.number_of_demands = 0
        self.time_interval = 0.0

    def __repr__(self):
        return f"Time interval: {self.time_interval} | Number of demands: {self.number_of_demands}"


class Demand:
    def __init__(self):
        self.id = 0

        self.arrival_time = 0.0
        self.departure_time = 0.0
        self.service_time = 0.0
        self.service_start_time = 0.0

    def __repr__(self):
        return f"Demand id: {self.id} | Arrival_time: {self.arrival_time} | Service time: {self.service_time} | Departure time: {self.departure_time} | Service start time: {self.service_start_time}"


class Statistic:
    def __init__(self):
        self.simulation_demands_status = {}
        self.simulation_status_of_demands_number = []

        self.u_result = []
        self.w_result = []
        self.pk_result = []
        self.b_result = []

    def updateStatistic_arrival(self, demand):
        self.simulation_demands_status[demand.id] = demand

    def updateStatistic_departure(self, demand, departure_time, service_time, service_start_time):

        demand.departure_time = departure_time
        demand.service_time = service_time
        demand.service_start_time = service_start_time

        self.simulation_demands_status[demand.id] = demand

    def get_u(self, num_of_demands):
        tempTimes = []

        for i in range(1, num_of_demands + 1):
            demand = self.simulation_demands_status[i]
            time_in_system = demand.departure_time - demand.arrival_time
            if (time_in_system > 0):
                tempTimes.append(time_in_system)

        return sum(tempTimes) / num_of_demands

    def get_w(self, num_of_demands):
        tempTimes = []

        for i in range(1, num_of_demands + 1):
            demand = self.simulation_demands_status[i]
            time_in_queue = demand.service_start_time - demand.arrival_time
            if (time_in_queue > 0):
                tempTimes.append(time_in_queue)

        return sum(tempTimes) / num_of_demands

    def get_pk(self, model_time):
        pnSums = {}

        for ti in self.simulation_status_of_demands_number:
            if ti.number_of_demands in pnSums.keys():
                pnSums[ti.number_of_demands] += ti.time_interval
            else:
                pnSums[ti.number_of_demands] = ti.time_interval

        return {key: time_interval_sum / model_time for key, time_interval_sum in pnSums.items()}

    def get_b(self, num_of_demands, model_time):
        tempTimes = []

        for i in range(1, num_of_demands + 1):
            demand = self.simulation_demands_status[i]
            time_in_queue = demand.service_start_time - demand.arrival_time
            if (time_in_queue > 0):
                tempTimes.append(time_in_queue)

        return sum(tempTimes) / model_time

    def get_n(self, pk):
        n = 0.0
        for k, p in pk.items():
            n += p * k

        return n


class Simulation:
    def __init__(self):
        self.statistic = Statistic()
        self.arrival_rate = 0.0
        self.service_rate = 0.0
        self.batch_size = 1

        self.num_in_system = 0

        self.clock = 0.0
        self.t_arrival = 0.0
        self.t_depart = float('inf')

        self.num_arrivals = 0
        self.num_departs = 0
        self.total_wait = 0.0

        self.service_times = []

        self.arrival_id = 0

        self.queue = queue.LifoQueue()

    def advance_time(self):
        t_event = min(self.t_arrival, self.t_depart)

        self.total_wait += self.num_in_system * (t_event - self.clock)

        previous_clock = self.clock
        self.clock = t_event

        demandNumberTimeInterval = DemandNumberTimeInterval()
        demandNumberTimeInterval.time_interval = self.clock - previous_clock
        demandNumberTimeInterval.number_of_demands = self.num_in_system
        self.statistic.simulation_status_of_demands_number.append(
            demandNumberTimeInterval)

        if self.t_arrival <= self.t_depart:
            self.handle_arrival_event()
        else:
            self.handle_depart_event()

    def handle_arrival_event(self):
        self.arrival_id += 1
        self.num_in_system += 1
        self.num_arrivals += 1

        demand = Demand()

        demand.id = self.arrival_id
        demand.arrival_time = self.t_arrival

        self.statistic.updateStatistic_arrival(demand)
        self.queue.put(demand)

        if self.num_in_system >= self.batch_size and self.t_depart == float("inf"):
            service_time = self.generate_service()
            self.t_depart = self.t_arrival + service_time

            for i in range(self.batch_size):
                self.statistic.updateStatistic_departure(
                    self.queue.queue[i], self.t_depart, service_time, self.clock)

            self.service_times.append(service_time)

        self.t_arrival = self.clock + self.generate_interarrival()

    def handle_depart_event(self):
        self.num_in_system -= self.batch_size
        self.num_departs += self.batch_size

        for i in range(self.batch_size):
            self.queue.get()

        if self.num_in_system >= self.batch_size:
            service_time = self.generate_service()
            self.t_depart = self.clock + service_time

            for i in range(self.batch_size):
                self.statistic.updateStatistic_departure(
                    self.queue.queue[i], self.t_depart, service_time, self.clock)

            self.service_times.append(service_time)
        else:
            self.t_depart = float('inf')

    def generate_interarrival(self):
        return np.random.exponential(1.0/self.arrival_rate)

    def generate_service(self):
        return np.random.exponential(1.0/self.service_rate)


def get_simulation_results(time_ticks, arrival_rate, service_rate, batch_size):
    s = Simulation()
    s.arrival_rate = arrival_rate
    s.service_rate = service_rate
    s.batch_size = batch_size

    for i in range(time_ticks):
        s.advance_time()

    u = s.statistic.get_u(s.num_arrivals)
    w = s.statistic.get_w(s.num_arrivals)
    pk = s.statistic.get_pk(s.clock)
    n = s.statistic.get_n(pk)
    utilization = sum(s.service_times) / s.clock
    b = s.statistic.get_b(s.num_arrivals, s.clock)

    demands_count = s.num_arrivals

    return {
        'demands_count': demands_count,
        'u': u,
        'w': w,
        'pk': pk,
        'n': n,
        'b': b,
        'utilization': utilization,
    }
