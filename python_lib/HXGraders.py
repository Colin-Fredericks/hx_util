import json
import math

def videoWatchGrader(ans, grading):

    # Get the student's answer.
    parsed = json.loads(ans)
    answer = json.loads(parsed['answer'])
    video_length = float(answer['video_length'])
    watch_times = answer['watch_times']
    start_time = float(answer['start_time'])

    durations = []
    total_watch_time = 0
    end_time = 0
    grade = 0

    # Remove duplicates and sort the list
    watch_times = [float(i) for i in watch_times]
    watch_times = list(set(watch_times))
    watch_times.sort()

    # Count up the times
    for j in watch_times:

        ind = watch_times.index(j)
        this_time = j

        next_time = watch_times[ind + 1]

        # If the next one is the last item, mark it as an end and we're done.
        if ind == len(watch_times) - 2:
            end_time = next_time
            durations.append(end_time - start_time)
            break

        # If the next time is too far ahead, call this an end and push duration
        elif next_time - this_time > 2:
            end_time = this_time
            durations.append(end_time - start_time)
            start_time = next_time

        # If this is the first time, make sure we're using that as our start time.
        elif ind == 0:
            start_time = this_time

        # Otherwise, just keep counting up.
        else:
            pass

    # Add up all the durations to get the total
    total_watch_time = sum(durations)

    grade = total_watch_time / video_length

    if grading == 'strict':
        grade = grade * grade
    elif grading == 'generous':
        grade = math.sqrt(grade)

    # Round up to the nearest tenth.
    grade = math.ceil(grade*10.0) / 10.0

    msg = "You watched about " + str(int(grade * 100)) + " percent of the video."

    if grade > 0.95:
        isOK = True
    elif grade > 0.20:
        isOK = "Partial"
    else:
        isOK = False

    return {
        'input_list': [
            {'ok': isOK, 'msg': msg, 'grade_decimal': grade},
        ]
    }
