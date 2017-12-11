import json
import math
import random

def textResponseGrader(ans, new_options = {'min_length': 10}):

    options = {'min_length': 10}
    options.update(new_options)

    parsed = json.loads(ans)
    answer = json.loads(parsed['answer'])['answer']

    # Remove quotes and whitespace from the ends.
    answer = answer.strip('"')
    answer = answer.strip('"')
    answer = answer.strip()

    if len(answer) >= options['min_length']:
        return {
            'input_list': [
                {'ok': True, 'msg': 'Thank you for your response.', 'grade_decimal': 1},
            ]
        }
    else:
        return {
            'input_list': [
                {'ok': False, 'msg': 'Your response is too short. Please try again.', 'grade_decimal': 0},
            ]
        }

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
        elif next_time - this_time > 3:
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
    grade = min(grade, 1.0)

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

#######################################################################
# The following block provides a grader for ordinal data.
# Scores are calculated using Levenshtein distances.
# Several helper functions are below (before the grader code),
# taken from https://www.python-course.eu/levenshtein_distance.php
#######################################################################

def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)
    helper.calls = 0
    helper.__name__= func.__name__
    return helper
def memoize(func):
    mem = {}
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in mem:
            mem[key] = func(*args, **kwargs)
        return mem[key]
    return memoizer
@call_counter
@memoize
def levenshtein(s, t):
    if s == "":
        return len(t)
    if t == "":
        return len(s)
    if s[-1] == t[-1]:
        cost = 0
    else:
        cost = 1

    res = min([levenshtein(s[:-1], t)+1,
               levenshtein(s, t[:-1])+1,
               levenshtein(s[:-1], t[:-1]) + cost])
    return res

def orderGrader(ans, right_answer,
    new_options = {'partial_credit': True, 'feedback': True, 'all_correct': False}):

  parsed = json.loads(ans)
  answer = json.loads(parsed['answer'])
  answer = answer['pairings']

  options = {'partial_credit': True, 'feedback': True, 'all_correct': False}
  options.update(new_options)

  if options['all_correct']:
    return {
      'input_list': [
        {'ok': True, 'msg': 'Thank you for your response.', 'grade_decimal': 1},
      ]
    }


  # We only care about the letters and their order in this problem type.
  # Make sure pairings are in order by number.
  answer_sort = sorted(answer, key=lambda x: x[1])
  # Make it one word for easy comparison.
  answer_word = ''.join([x[0] for x in answer_sort])

  currentpoints = []
  maxpoints = []
  scores = []

  for right_answer_n in right_answer:

    # Lose a point for every change that needs to happen
    # to make your sequence into the right one.
    lev_dist = levenshtein(answer_word.lower(), right_answer_n.lower())
    points = len(right_answer_n) - lev_dist

    currentpoints.append(points)
    maxpoints.append(len(right_answer_n))
    scores.append(float(currentpoints[-1]) / float(maxpoints[-1]))

  final_grade = max(scores)
  final_index = scores.index(final_grade)
  final_grade = round(final_grade, 2)
  final_grade = max(final_grade, 0)
  delta = maxpoints[final_index] - currentpoints[final_index]
  message = 'You are ' + str(delta)
  message += ' changes ' if delta > 1 else ' change '
  message += ' away from the ideal sequence.'

  is_right = False
  if 0.1 < final_grade < 0.9 and options['partial_credit']: is_right = 'Partial'
  elif final_grade >= 0.9: is_right = True

  # No points for placing just one item.
  if len(answer_word) == 1:
    message = 'Only one item placed.'
    final_grade = 0
    is_right = False

  if final_grade == 1: message = 'This sequence is correct.'

  if not options['feedback']: message = ''

  return {
    'input_list': [
      { 'ok': is_right, 'msg': message, 'grade_decimal': final_grade},
    ]
  }

def rangeGuessGrader(ans, options):

  # Get the student's answer.
  parsed = json.loads(ans)
  answer = json.loads(parsed['answer'])
  guess_upper = answer['upperguess']
  guess_lower = answer['lowerguess']
  guess_upper_closed = answer['upperclosed']
  guess_lower_closed = answer['lowerclosed']

  # Now begins the grading.
  message = ''
  final_grade = 0

  if options['problem_type'] == 'interval':
    if guess_upper < options['correct_interval'][0]:
      # No points if there's no overlap.
      message = 'Answer not in selected range.'
    elif guess_lower > options['correct_interval'][1]:
      # Same here.
      message = 'Answer not in selected range.'
    else:
      # Points based on percentage overlap.
      endpoints = []
      endpoints.append(options['correct_interval'][0])
      endpoints.append(options['correct_interval'][1])
      endpoints.append(guess_upper)
      endpoints.append(guess_lower)
      endpoints.sort()

      overlap = endpoints[2] - endpoints[1]
      bigrange = max(options['correct_interval'][1] - options['correct_interval'][0], guess_upper - guess_lower)
      final_grade = float(overlap) / float(bigrange)

      message = str(int(round(final_grade, 2) * 100)) + '% overlap with correct answer.'

      if options['interval_tolerance'] == 'strict':
        final_grade = final_grade * final_grade
      elif options['interval_tolerance'] == 'generous':
        final_grade = math.sqrt(final_grade)

      # Round up to the nearest tenth.
      final_grade = math.ceil(final_grade*10.0) / 10.0

      if options['show_open_close']:
        if(guess_lower_closed != True and options['interval_type'][0] == 'closed'):
          final_grade = final_grade - options['type_penalty']
          message += ' Lower endpoint is wrong.'
        if(guess_lower_closed == True and options['interval_type'][0] != 'closed'):
          final_grade = final_grade - options['type_penalty']
          message += ' Lower endpoint is wrong.'
        if(guess_upper_closed != True and options['interval_type'][1] == 'closed'):
          final_grade = final_grade - options['type_penalty']
          message += ' Upper endpoint is wrong.'
        if(guess_upper_closed == True and options['interval_type'][1] != 'closed'):
          final_grade = final_grade - options['type_penalty']
          message += ' Upper endpoint is wrong.'

  else:

    farthest = max(abs(options['correct_number'] - guess_upper), abs(options['correct_number'] - guess_lower))

    if farthest < options['tolerance'][0]:
      final_grade = options['brackets'][0]
      message = 'Close enough! Actual answer: ' + str(options['correct_number'])
    elif farthest < options['tolerance'][1]:
      final_grade = options['brackets'][1]
      message = 'Close. You are off by ' + str(farthest)
    elif farthest < options['tolerance'][2]:
      final_grade = options['brackets'][2]
      message = 'Not very close. You are off by ' + str(farthest)
    else:
      final_grade = options['brackets'][3]
      message = 'Your range is too large to get points.'

    if guess_upper > options['correct_number'] and guess_lower < options['correct_number']:
      message += ' The answer is within your range.'
    else:
      message += ' The answer is outside your range.'

  if not options['feedback']:
    message = ''

  if final_grade > 0.95:
    isOK = True
  elif final_grade > 0.05:
    isOK = "Partial"
  else:
    isOK = False

  return {
    'input_list': [
        { 'ok': isOK, 'msg': message, 'grade_decimal': final_grade},
    ]
  }

def getRangeGuesserParams(options):

  # Set the outer bounds for the slider
  if options['problem_type'] == 'interval':
    range = options['correct_interval'][1] - options['correct_interval'][0]
    lowerlimit = options['correct_interval'][0] - 2 * range * (random.random() + 1)
    upperlimit = options['correct_interval'][1] + 2 * range * (random.random() + 1)
  else:
    range = options['tolerance'][2]
    lowerlimit = options['correct_number'] - 2 * range * (random.random() + 1)
    upperlimit = options['correct_number'] + 2 * range * (random.random() + 1)

  return {'upper': upperlimit, 'lower': lowerlimit}
