import numpy as np


class SingleQueuePmf:
    def __init__(self):
        self.pmf_list = [1]

    def arrival_step(self, arrival_prob=0.2):
        arrival_prob = max(min(arrival_prob, 1), 0)
        no_arrival_list = self.pmf_list + [0]
        with_arrival_list = [0] + self.pmf_list
        new_pmf_list = np.array(no_arrival_list) * (1 - arrival_prob)
        new_pmf_list += np.array(with_arrival_list) * arrival_prob
        new_pmf_list = new_pmf_list.tolist()

        self.pmf_list = new_pmf_list
        self.remove_tail()
        return self.pmf_list

    def departure_step(self, departure_prob=0):
        departure_prob = max(min(departure_prob, 1), 0)
        no_residual_prob = self.pmf_list[0]
        with_departure_list = self.pmf_list[1:] + [0]
        with_departure_list[0] += no_residual_prob
        no_departure_list = self.pmf_list
        new_pmf_list = np.array(with_departure_list) * departure_prob
        new_pmf_list += np.array(no_departure_list) * (1 - departure_prob)
        new_pmf_list = new_pmf_list.tolist()
        self.pmf_list = new_pmf_list
        self.remove_tail()
        return (1 - no_residual_prob) * departure_prob

    def get_mean(self):
        return sum([idx * self.pmf_list[idx] for idx in range(len(self.pmf_list))])

    def get_prob(self, arrivals):
        """
        probability that the arrival is larger (equivalent) than certain value

        :param arrivals:
        :return:
        """
        cum_prob = 0
        for i_arrival in range(len(self.pmf_list)):
            if i_arrival >= arrivals:
                cum_prob += self.pmf_list[i_arrival]
        return cum_prob

    def with_residual_prob(self):
        return self.get_prob(1)

    def remove_tail(self, prop=1e-3):
        total_prob = 0
        cut_index = 0
        for cut_index in range(len(self.pmf_list)):
            total_prob += self.pmf_list[cut_index]
            if total_prob >= 1 - prop:
                break
        self.pmf_list = self.pmf_list[:cut_index + 1]
        scale_coefficient = 1.0 / sum(self.pmf_list)
        self.pmf_list = [val * scale_coefficient for val in self.pmf_list]




