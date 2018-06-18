import math

class HeartbeatHistory():
    def __init__(self, maxSampleSize):
        if maxSampleSize < 1:
            raise ValueError("MaxSampleSize must be >= 1, got " + str(maxSampleSize))
        self.maxSampleSize = maxSampleSize
        self.intervals = list()
        self.intervalSum = 0.0
        self.squaredIntervalSum = 0.0

    def mean(self):
        result = self.intervalSum / float(len(self.intervals))
        return result

    def variance(self):
        mean = self.mean()
        return (self.squaredIntervalSum / float(len(self.intervals))) - (mean * mean)

    def stdDeviation(self):
        current_variance = self.variance()
        return math.sqrt(current_variance)

    def add(self, interval):
        if len(self.intervals) > self.maxSampleSize:
            dropped = self.intervals.pop(0)
            self.intervalSum -= dropped
            self.squaredIntervalSum -= dropped ** 2
        self.intervals.append(interval)
        self.intervalSum += interval
        self.squaredIntervalSum += interval ** 2


class PhiAccrualFailureDetector():
    def __init__(self, threshold = 0.4, maxSampleSize = 200, minStdDeviationMillis = 500, acceptableHeartbeatPauseMillis = 0, firstHeartbeatEstimateMillis = 500):
        if (threshold <= 0):
            raise ValueError("Threshold must be greater than 0, got: " + str(threshold))

        if (maxSampleSize <= 0):
            raise ValueError("maxSampleSize must be greater than 0, got: " + str(maxSampleSize))

        if (minStdDeviationMillis <= 0):
            raise ValueError("minStdDeviation must be greateer than 0, got: " + str(minStdDeviation))

        if (acceptableHeartbeatPauseMillis < 0):
            raise ValueError("acceptableHeartbeatPauseMillis must be greater than or equal to 0, got: " + str(acceptableHeartbeatPauseMillis))

        if (firstHeartbeatEstimateMillis <= 0):
            raise ValueError("firstHeartbeatEstimateMillis must be greater than or equal to 0, got: " + str(firstHeartbeatEstimateMillis))


        self.threshold = threshold
        self.minStdDeviationMillis = minStdDeviationMillis
        self.acceptableHeartbeatPauseMillis = acceptableHeartbeatPauseMillis

        stdDeviationMillis = firstHeartbeatEstimateMillis / 4
        self.heartbeatHistory = HeartbeatHistory(maxSampleSize)
        self.heartbeatHistory.add(firstHeartbeatEstimateMillis - stdDeviationMillis)
        self.heartbeatHistory.add(firstHeartbeatEstimateMillis + stdDeviationMillis)

        self.lastTimestampMillis = None

    def ensureValidStdDeviation(self, stdDeviationMillis):
        return max(stdDeviationMillis, self.minStdDeviationMillis)

    def phi(self, timestampMillis):
        if (self.lastTimestampMillis == None):
            return 0.0

        timeDiffMillis = timestampMillis - self.lastTimestampMillis
        meanMillis = self.heartbeatHistory.mean() + self.acceptableHeartbeatPauseMillis
        stdDeviationMillis = self.ensureValidStdDeviation(self.heartbeatHistory.stdDeviation())

        y = (timeDiffMillis - meanMillis) / stdDeviationMillis
        e = math.exp(-y * (1.5976 + 0.070566 * y * y))

        if (timeDiffMillis > meanMillis):
            return -math.log10(e / (1.0 + e))
        else:
            return -math.log10(1.0 - 1.0 / (1.0 + e))

    def isAvailable(self, timestampMillis):
        try:
            return self.phi(timestampMillis) < self.threshold
        except ValueError:
            return 0

    def heartbeat(self, timestampMillis):
        if (self.lastTimestampMillis is not None):
            interval = timestampMillis - self.lastTimestampMillis
            if (self.isAvailable(timestampMillis)):
                self.heartbeatHistory.add(interval)

        self.lastTimestampMillis = timestampMillis
        
