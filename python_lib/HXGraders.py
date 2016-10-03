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


def matchingAGrader(ans, right_answer, partial_credit, feedback):
  
  parsed = json.loads(ans)
  answer = json.loads(parsed['answer'])
  answer = answer['pairings']
  
  if partial_credit:
  
    currentpoints = []
    wrong_answers = []
    maxpoints = []
    scores = []
    answer_index = 0
  
    for right_answer_n in right_answer:

      maxpoints.append(len(right_answer_n))
      currentpoints.append(0)
      wrong_answers.append(0)
      
      for item in answer:
        does_match = False
        for target in right_answer_n:
          if item == target:
            does_match = True
            break
        if does_match:
          currentpoints[answer_index] += 1
        else:
          wrong_answers[answer_index] += 1
          
    
      scores.append((float(currentpoints[answer_index] - wrong_answers[answer_index])) / float(maxpoints[answer_index]))
      answer_index += 1
  
    final_grade = max(scores)
    final_index = scores.index(final_grade)
    final_grade = round(final_grade, 2)
    final_grade = max(final_grade, 0)
    message = str(currentpoints[final_index]) 
    message += ' correct out of ' 
    message += str(maxpoints[final_index]) 
    message += ', ' 
    message += str(wrong_answers[final_index]) 
    message += ' wrong.'

    is_right = False
    if 0.1 < final_grade < 0.9: is_right = 'Partial'
    elif final_grade >= 0.9: is_right = True
    
    if not feedback: message = ''
    
    return {
      'input_list': [
        { 'ok': is_right, 'msg': message, 'grade_decimal': final_grade},
      ]
    }
  
  else:
    answer_sort = sorted(answer)
  
    is_right = False
  
    for right_answer_n in right_answer:
      right_answer_sort = sorted(right_answer_n)
  
      if answer_sort == right_answer_sort:
        is_right = True
        break
      else:
        is_right = False
        
    return is_right
