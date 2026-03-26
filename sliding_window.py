from collections import deque

window = deque()
freq = {}

def add_event(timestamp, keyword, window_size):
    window.append((timestamp, keyword))
    freq[keyword] = freq.get(keyword, 0) + 1
    remove_expired(timestamp, window_size)

def remove_expired(current_time, window_size):
    while window and window[0][0] <= current_time - window_size:
        old_timestamp, old_keyword = window.popleft()
        freq[old_keyword] -= 1
        if freq[old_keyword] == 0:
            del freq[old_keyword]

def get_frequencies():
    return dict(freq)

add_event(1, "jeans")
print(get_frequencies())

add_event(2, "tops")
print(get_frequencies())

add_event(3, "jeans")
print(get_frequencies())

add_event(4, "shoes")
print(get_frequencies())

add_event(5, "tops")
print(get_frequencies())
