import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend path is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models.topic import Topic
from app.models.problem import Problem, ProblemDifficulty
from app.models.problem_topic import ProblemTopic
from app.models.test_case import TestCase

# 12 Initial Topics with useful descriptions
TOPICS_SEED_DATA = [
    {"name": "Arrays", "description": "Fundamental contiguous memory data structures and array manipulation algorithms."},
    {"name": "Strings", "description": "String parsing, pattern matching, transformation, and character array operations."},
    {"name": "Hashing", "description": "Fast key-value lookup, frequency counting, and set operations using Hash Maps."},
    {"name": "Two Pointers", "description": "Efficient search and comparison techniques using two array index pointers."},
    {"name": "Sliding Window", "description": "Subarray and substring tracking algorithms over fixed or dynamic window sizes."},
    {"name": "Stack & Queue", "description": "LIFO stack and FIFO queue linear data structure operations."},
    {"name": "Linked List", "description": "Sequential node chain manipulation, reversal, and pointer reordering."},
    {"name": "Binary Search", "description": "Logarithmic O(log N) search algorithms on sorted arrays and search spaces."},
    {"name": "Trees", "description": "Hierarchical tree structures, Binary Search Trees (BST), and tree traversals."},
    {"name": "Graphs", "description": "Node & edge networks, Breadth-First Search (BFS), and Depth-First Search (DFS)."},
    {"name": "Greedy", "description": "Local optimal choice strategy for global optimization problems."},
    {"name": "Dynamic Programming", "description": "Optimization via overlapping subproblems and memoization/tabulation."},
]

# 36 Problems (1 EASY, 1 MEDIUM, 1 HARD for each of the 12 topics)
PROBLEMS_SEED_DATA: List[Dict[str, Any]] = [
    # 1. Arrays
    {
        "topic": "Arrays",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Find Maximum Element in Array",
        "slug": "find-maximum-element-in-array",
        "description": "Given an unsorted array of N integers, what is the worst-case time complexity of finding the maximum element by scanning through the array?",
        "constraints": "1 <= nums.length <= 10^5\n-10^9 <= nums[i] <= 10^9",
        "input_format": "The first line contains space-separated integers representing `nums`.",
        "output_format": "Return a single integer representing the maximum element.",
        "examples": [
            {"input": "1 5 3 9 2", "output": "9", "explanation": "9 is the maximum value in the array."}
        ],
        "starter_code": {"python": "def solve(nums: list[int]) -> int:\n    # Write your solution here\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. O(1)", "B. O(log N)", "C. O(N)", "D. O(N^2)"],
        "diagnostic_correct_option": "C",
        "options": ["A. O(1)", "B. O(log N)", "C. O(N)", "D. O(N^2)"],
        "correct_option": "C",
        "test_cases": [
            {"input": "1 5 3 9 2", "expected_output": "9", "is_hidden": False},
            {"input": "-10 -5 -20 -1", "expected_output": "-1", "is_hidden": True},
            {"input": "42", "expected_output": "42", "is_hidden": True},
        ]
    },
    {
        "topic": "Arrays",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Rotate Array by K Steps",
        "slug": "rotate-array-by-k-steps",
        "description": "Given an array `nums` and a non-negative integer `k`, rotate the array to the right by `k` steps.",
        "constraints": "1 <= nums.length <= 10^5\n0 <= k <= 10^5",
        "input_format": "Line 1: space-separated integers `nums`. Line 2: integer `k`.",
        "output_format": "Return space-separated integers of the rotated array.",
        "examples": [
            {"input": "1 2 3 4 5 6 7\n3", "output": "5 6 7 1 2 3 4", "explanation": "Rotating right 3 steps gives [5, 6, 7, 1, 2, 3, 4]."}
        ],
        "starter_code": {"python": "def solve(nums: list[int], k: int) -> list[int]:\n    # Write your solution here\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 2 3 4 5 6 7\n3", "expected_output": "5 6 7 1 2 3 4", "is_hidden": False},
            {"input": "-1 -100 3 99\n2", "expected_output": "3 99 -1 -100", "is_hidden": True},
        ]
    },
    {
        "topic": "Arrays",
        "difficulty": ProblemDifficulty.HARD,
        "title": "First Missing Positive Integer",
        "slug": "first-missing-positive-integer",
        "description": "Given an unsorted integer array `nums`, return the smallest positive integer that is not present in `nums` in O(N) time.",
        "constraints": "1 <= nums.length <= 10^5\n-2^31 <= nums[i] <= 2^31 - 1",
        "input_format": "Space-separated integers.",
        "output_format": "Single positive integer.",
        "examples": [
            {"input": "1 2 0", "output": "3", "explanation": "1 and 2 are present, smallest missing positive is 3."}
        ],
        "starter_code": {"python": "def solve(nums: list[int]) -> int:\n    # Write your solution here\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 2 0", "expected_output": "3", "is_hidden": False},
            {"input": "3 4 -1 1", "expected_output": "2", "is_hidden": True},
            {"input": "7 8 9 11 12", "expected_output": "1", "is_hidden": True},
        ]
    },

    # 2. Strings
    {
        "topic": "Strings",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Reverse String",
        "slug": "reverse-string",
        "description": "Which algorithmic technique allows reversing a string in-place with O(1) auxiliary space by swapping characters from both ends moving inward?",
        "constraints": "1 <= s.length <= 10^5",
        "input_format": "Single string `s`.",
        "output_format": "Reversed string.",
        "examples": [{"input": "hello", "output": "olleh", "explanation": "Reversing 'hello' gives 'olleh'."}],
        "starter_code": {"python": "def solve(s: str) -> str:\n    return s[::-1]"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. Two Pointers", "B. Recursion with call stack", "C. Hash Map lookup", "D. Queue buffering"],
        "diagnostic_correct_option": "A",
        "options": ["A. Two Pointers", "B. Recursion with call stack", "C. Hash Map lookup", "D. Queue buffering"],
        "correct_option": "A",
        "test_cases": [
            {"input": "hello", "expected_output": "olleh", "is_hidden": False},
            {"input": "CodeArena", "expected_output": "anerAedoC", "is_hidden": True},
        ]
    },
    {
        "topic": "Strings",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Longest Palindromic Substring",
        "slug": "longest-palindromic-substring",
        "description": "Given a string `s`, return the longest palindromic substring in `s`.",
        "constraints": "1 <= s.length <= 1000",
        "input_format": "Single string `s`.",
        "output_format": "Longest palindromic substring.",
        "examples": [{"input": "babad", "output": "bab", "explanation": "'aba' is also a valid answer."}],
        "starter_code": {"python": "def solve(s: str) -> str:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "babad", "expected_output": "bab", "is_hidden": False},
            {"input": "cbbd", "expected_output": "bb", "is_hidden": True},
        ]
    },
    {
        "topic": "Strings",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Regular Expression Matching",
        "slug": "regular-expression-matching",
        "description": "Implement regex pattern matching supporting `.` (any char) and `*` (zero or more preceding element).",
        "constraints": "1 <= s.length, p.length <= 20",
        "input_format": "Line 1: string `s`. Line 2: pattern `p`.",
        "output_format": "true or false",
        "examples": [{"input": "aa\na*", "output": "true", "explanation": "'a*' matches 'aa'."}],
        "starter_code": {"python": "def solve(s: str, p: str) -> bool:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "aa\na*", "expected_output": "true", "is_hidden": False},
            {"input": "ab\n.*", "expected_output": "true", "is_hidden": True},
        ]
    },

    # 3. Hashing
    {
        "topic": "Hashing",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Two Sum Target Pair",
        "slug": "two-sum-target-pair",
        "description": "When solving Two Sum by scanning N elements once and using a Hash Map to store each element and check whether its complement exists, what is the average time complexity of the complete algorithm?",
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9",
        "input_format": "Line 1: space-separated integers `nums`. Line 2: integer `target`.",
        "output_format": "Two space-separated indices.",
        "examples": [{"input": "2 7 11 15\n9", "output": "0 1", "explanation": "nums[0] + nums[1] == 9"}],
        "starter_code": {"python": "def solve(nums: list[int], target: int) -> list[int]:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. O(1)", "B. O(N)", "C. O(N log N)", "D. O(N^2)"],
        "diagnostic_correct_option": "B",
        "options": ["A. O(1)", "B. O(N)", "C. O(N log N)", "D. O(N^2)"],
        "correct_option": "B",
        "test_cases": [
            {"input": "2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False},
            {"input": "3 2 4\n6", "expected_output": "1 2", "is_hidden": True},
        ]
    },
    {
        "topic": "Hashing",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Group Anagrams Together",
        "slug": "group-anagrams-together",
        "description": "Given an array of strings `strs`, group the anagrams together.",
        "constraints": "1 <= strs.length <= 10^4",
        "input_format": "Space separated strings.",
        "output_format": "Count of unique anagram groups.",
        "examples": [{"input": "eat tea tan ate nat bat", "output": "3", "explanation": "Groups: [eat, tea, ate], [tan, nat], [bat]"}],
        "starter_code": {"python": "def solve(strs: list[str]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "eat tea tan ate nat bat", "expected_output": "3", "is_hidden": False},
            {"input": "a", "expected_output": "1", "is_hidden": True},
        ]
    },
    {
        "topic": "Hashing",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Longest Consecutive Sequence",
        "slug": "longest-consecutive-sequence",
        "description": "Given an unsorted array of integers `nums`, return the length of the longest consecutive elements sequence in O(N) time.",
        "constraints": "0 <= nums.length <= 10^5",
        "input_format": "Space-separated integers.",
        "output_format": "Length of longest consecutive sequence.",
        "examples": [{"input": "100 4 200 1 3 2", "output": "4", "explanation": "Sequence is [1, 2, 3, 4]."}],
        "starter_code": {"python": "def solve(nums: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "100 4 200 1 3 2", "expected_output": "4", "is_hidden": False},
            {"input": "0 3 7 2 5 8 4 6 0 1", "expected_output": "9", "is_hidden": True},
        ]
    },

    # 4. Two Pointers
    {
        "topic": "Two Pointers",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Valid Palindrome String",
        "slug": "valid-palindrome-string",
        "description": "When checking if a string of length N is a palindrome using two pointers moving towards the center, what is the auxiliary space complexity of the algorithm?",
        "constraints": "1 <= s.length <= 2 * 10^5",
        "input_format": "Single string `s`.",
        "output_format": "true or false",
        "examples": [{"input": "A man, a plan, a canal: Panama", "output": "true", "explanation": "'amanaplanacanalpanama' is a palindrome."}],
        "starter_code": {"python": "def solve(s: str) -> bool:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. O(N)", "B. O(1)", "C. O(N log N)", "D. O(N^2)"],
        "diagnostic_correct_option": "B",
        "options": ["A. O(N)", "B. O(1)", "C. O(N log N)", "D. O(N^2)"],
        "correct_option": "B",
        "test_cases": [
            {"input": "A man, a plan, a canal: Panama", "expected_output": "true", "is_hidden": False},
            {"input": "race a car", "expected_output": "false", "is_hidden": True},
        ]
    },
    {
        "topic": "Two Pointers",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Container With Most Water",
        "slug": "container-with-most-water",
        "description": "Given `n` non-negative integers `height`, find two lines that together with x-axis forms a container holding most water.",
        "constraints": "2 <= height.length <= 10^5",
        "input_format": "Space-separated height values.",
        "output_format": "Maximum area of water.",
        "examples": [{"input": "1 8 6 2 5 4 8 3 7", "output": "49", "explanation": "Max area between index 1 and 8."}],
        "starter_code": {"python": "def solve(height: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 8 6 2 5 4 8 3 7", "expected_output": "49", "is_hidden": False},
            {"input": "1 1", "expected_output": "1", "is_hidden": True},
        ]
    },
    {
        "topic": "Two Pointers",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Trapping Rain Water",
        "slug": "trapping-rain-water",
        "description": "Given `n` non-negative integers representing an elevation map where width of each bar is 1, compute how much water it can trap after raining.",
        "constraints": "1 <= height.length <= 2 * 10^4",
        "input_format": "Space-separated height values.",
        "output_format": "Total units of trapped water.",
        "examples": [{"input": "0 1 0 2 1 0 1 3 2 1 2 1", "output": "6", "explanation": "6 units of water trapped."}],
        "starter_code": {"python": "def solve(height: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "0 1 0 2 1 0 1 3 2 1 2 1", "expected_output": "6", "is_hidden": False},
            {"input": "4 2 0 3 2 5", "expected_output": "9", "is_hidden": True},
        ]
    },

    # 5. Sliding Window
    {
        "topic": "Sliding Window",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Maximum Average Subarray I",
        "slug": "maximum-average-subarray-i",
        "description": "What is the time complexity of computing the maximum sum among all contiguous subarrays of fixed size K in an array of size N using a sliding window?",
        "constraints": "1 <= k <= nums.length <= 10^5",
        "input_format": "Line 1: space-separated `nums`. Line 2: integer `k`.",
        "output_format": "Maximum average formatted to 2 decimal places.",
        "examples": [{"input": "1 12 -5 -6 50 3\n4", "output": "12.75", "explanation": "Subarray [12, -5, -6, 50] has max sum 51."}],
        "starter_code": {"python": "def solve(nums: list[int], k: int) -> float:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. O(N * K)", "B. O(N)", "C. O(K^2)", "D. O(N log N)"],
        "diagnostic_correct_option": "B",
        "options": ["A. O(N * K)", "B. O(N)", "C. O(K^2)", "D. O(N log N)"],
        "correct_option": "B",
        "test_cases": [
            {"input": "1 12 -5 -6 50 3\n4", "expected_output": "12.75", "is_hidden": False},
            {"input": "5\n1", "expected_output": "5.00", "is_hidden": True},
        ]
    },
    {
        "topic": "Sliding Window",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Longest Substring Without Repeating Characters",
        "slug": "longest-substring-without-repeating-characters",
        "description": "Given a string `s`, find the length of the longest substring without repeating characters.",
        "constraints": "0 <= s.length <= 5 * 10^4",
        "input_format": "Single string `s`.",
        "output_format": "Integer length.",
        "examples": [{"input": "abcabcbb", "output": "3", "explanation": "The answer is 'abc', length 3."}],
        "starter_code": {"python": "def solve(s: str) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "abcabcbb", "expected_output": "3", "is_hidden": False},
            {"input": "bbbbb", "expected_output": "1", "is_hidden": True},
        ]
    },
    {
        "topic": "Sliding Window",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Minimum Window Substring",
        "slug": "minimum-window-substring",
        "description": "Given two strings `s` and `t`, return the minimum window substring of `s` such that every character in `t` is included in the window.",
        "constraints": "1 <= s.length, t.length <= 10^5",
        "input_format": "Line 1: string `s`. Line 2: string `t`.",
        "output_format": "Minimum window substring.",
        "examples": [{"input": "ADOBECODEBANC\nABC", "output": "BANC", "explanation": "Minimum window containing 'A', 'B', 'C' is 'BANC'."}],
        "starter_code": {"python": "def solve(s: str, t: str) -> str:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "ADOBECODEBANC\nABC", "expected_output": "BANC", "is_hidden": False},
            {"input": "a\na", "expected_output": "a", "is_hidden": True},
        ]
    },

    # 6. Stack & Queue
    {
        "topic": "Stack & Queue",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Valid Parentheses String",
        "slug": "valid-parentheses-string",
        "description": "Which linear data structure is best suited for checking matching pairs of nested opening and closing parentheses in an expression (LIFO order)?",
        "constraints": "1 <= s.length <= 10^4",
        "input_format": "String of brackets.",
        "output_format": "true or false",
        "examples": [{"input": "()[]{}", "output": "true", "explanation": "All brackets close in correct order."}],
        "starter_code": {"python": "def solve(s: str) -> bool:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. Queue", "B. Stack", "C. Heap", "D. Hash Table"],
        "diagnostic_correct_option": "B",
        "options": ["A. Queue", "B. Stack", "C. Heap", "D. Hash Table"],
        "correct_option": "B",
        "test_cases": [
            {"input": "()[]{}", "expected_output": "true", "is_hidden": False},
            {"input": "(]", "expected_output": "false", "is_hidden": True},
        ]
    },
    {
        "topic": "Stack & Queue",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Evaluate Reverse Polish Notation",
        "slug": "evaluate-reverse-polish-notation",
        "description": "Evaluate the value of an arithmetic expression in Reverse Polish Notation (Postfix).",
        "constraints": "1 <= tokens.length <= 10^4",
        "input_format": "Space separated tokens.",
        "output_format": "Single integer evaluation result.",
        "examples": [{"input": "2 1 + 3 *", "output": "9", "explanation": "((2 + 1) * 3) = 9"}],
        "starter_code": {"python": "def solve(tokens: list[str]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "2 1 + 3 *", "expected_output": "9", "is_hidden": False},
            {"input": "4 13 5 / +", "expected_output": "6", "is_hidden": True},
        ]
    },
    {
        "topic": "Stack & Queue",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Largest Rectangle in Histogram",
        "slug": "largest-rectangle-in-histogram",
        "description": "Given an array of integers `heights` representing histogram bar heights, return area of largest rectangle in histogram.",
        "constraints": "1 <= heights.length <= 10^5",
        "input_format": "Space separated bar heights.",
        "output_format": "Maximum rectangle area.",
        "examples": [{"input": "2 1 5 6 2 3", "output": "10", "explanation": "Largest rectangle between index 2 and 3 area = 5*2 = 10."}],
        "starter_code": {"python": "def solve(heights: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "2 1 5 6 2 3", "expected_output": "10", "is_hidden": False},
            {"input": "2 4", "expected_output": "4", "is_hidden": True},
        ]
    },

    # 7. Linked List
    {
        "topic": "Linked List",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Reverse Singly Linked List",
        "slug": "reverse-singly-linked-list",
        "description": "In the standard iterative algorithm for reversing a singly linked list, which three references are maintained to reverse the links safely?",
        "constraints": "0 <= list.length <= 5000",
        "input_format": "Space separated node values.",
        "output_format": "Space separated reversed values.",
        "examples": [{"input": "1 2 3 4 5", "output": "5 4 3 2 1", "explanation": "Reversing linked list [1,2,3,4,5] gives [5,4,3,2,1]."}],
        "starter_code": {"python": "def solve(head: list[int]) -> list[int]:\n    return head[::-1]"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. head, tail, temp", "B. left, right, middle", "C. prev, current, next", "D. parent, child, sibling"],
        "diagnostic_correct_option": "C",
        "options": ["A. head, tail, temp", "B. left, right, middle", "C. prev, current, next", "D. parent, child, sibling"],
        "correct_option": "C",
        "test_cases": [
            {"input": "1 2 3 4 5", "expected_output": "5 4 3 2 1", "is_hidden": False},
            {"input": "1 2", "expected_output": "2 1", "is_hidden": True},
        ]
    },
    {
        "topic": "Linked List",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Remove Nth Node From End of List",
        "slug": "remove-nth-node-from-end-of-list",
        "description": "Given head of a linked list, remove the `n`-th node from the end of the list and return its head.",
        "constraints": "1 <= sz <= 30\n1 <= n <= sz",
        "input_format": "Line 1: space separated values. Line 2: integer `n`.",
        "output_format": "Space separated values after deletion.",
        "examples": [{"input": "1 2 3 4 5\n2", "output": "1 2 3 5", "explanation": "Removing 2nd node from end (4) leaves [1, 2, 3, 5]."}],
        "starter_code": {"python": "def solve(head: list[int], n: int) -> list[int]:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 2 3 4 5\n2", "expected_output": "1 2 3 5", "is_hidden": False},
            {"input": "1\n1", "expected_output": "", "is_hidden": True},
        ]
    },
    {
        "topic": "Linked List",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Merge K Sorted Linked Lists",
        "slug": "merge-k-sorted-linked-lists",
        "description": "You are given an array of `k` linked-lists, each sorted in ascending order. Merge all into one sorted list.",
        "constraints": "0 <= k <= 10^4",
        "input_format": "Line 1: integer `k`. Followed by `k` lines of space separated integers.",
        "output_format": "Merged sorted list.",
        "examples": [{"input": "3\n1 4 5\n1 3 4\n2 6", "output": "1 1 2 3 4 4 5 6", "explanation": "Merged list is sorted."}],
        "starter_code": {"python": "def solve(lists: list[list[int]]) -> list[int]:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "3\n1 4 5\n1 3 4\n2 6", "expected_output": "1 1 2 3 4 4 5 6", "is_hidden": False},
            {"input": "0", "expected_output": "", "is_hidden": True},
        ]
    },

    # 8. Binary Search
    {
        "topic": "Binary Search",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Standard Binary Search",
        "slug": "standard-binary-search",
        "description": "What is the worst-case time complexity of finding a target element in a sorted array of N elements using binary search?",
        "constraints": "1 <= nums.length <= 10^4",
        "input_format": "Line 1: space separated `nums`. Line 2: `target`.",
        "output_format": "Integer index or -1.",
        "examples": [{"input": "-1 0 3 5 9 12\n9", "output": "4", "explanation": "9 exists at index 4."}],
        "starter_code": {"python": "def solve(nums: list[int], target: int) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. O(N)", "B. O(log N)", "C. O(1)", "D. O(N log N)"],
        "diagnostic_correct_option": "B",
        "options": ["A. O(N)", "B. O(log N)", "C. O(1)", "D. O(N log N)"],
        "correct_option": "B",
        "test_cases": [
            {"input": "-1 0 3 5 9 12\n9", "expected_output": "4", "is_hidden": False},
            {"input": "-1 0 3 5 9 12\n2", "expected_output": "-1", "is_hidden": True},
        ]
    },
    {
        "topic": "Binary Search",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Search in Rotated Sorted Array",
        "slug": "search-in-rotated-sorted-array",
        "description": "Given a rotated sorted array `nums` and a target, return index of target or -1 in O(log N) time.",
        "constraints": "1 <= nums.length <= 5000",
        "input_format": "Line 1: space separated `nums`. Line 2: `target`.",
        "output_format": "Integer index or -1.",
        "examples": [{"input": "4 5 6 7 0 1 2\n0", "output": "4", "explanation": "0 is at index 4."}],
        "starter_code": {"python": "def solve(nums: list[int], target: int) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "4 5 6 7 0 1 2\n0", "expected_output": "4", "is_hidden": False},
            {"input": "4 5 6 7 0 1 2\n3", "expected_output": "-1", "is_hidden": True},
        ]
    },
    {
        "topic": "Binary Search",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Median of Two Sorted Arrays",
        "slug": "median-of-two-sorted-arrays",
        "description": "Given two sorted arrays `nums1` and `nums2` of size `m` and `n`, return the median of the two sorted arrays in O(log(m+n)).",
        "constraints": "0 <= m, n <= 1000",
        "input_format": "Line 1: space separated `nums1`. Line 2: space separated `nums2`.",
        "output_format": "Float median formatted to 1 decimal place.",
        "examples": [{"input": "1 3\n2", "output": "2.0", "explanation": "Merged array [1,2,3], median 2.0."}],
        "starter_code": {"python": "def solve(nums1: list[int], nums2: list[int]) -> float:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 3\n2", "expected_output": "2.0", "is_hidden": False},
            {"input": "1 2\n3 4", "expected_output": "2.5", "is_hidden": True},
        ]
    },

    # 9. Trees
    {
        "topic": "Trees",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Maximum Depth of Binary Tree",
        "slug": "maximum-depth-of-binary-tree",
        "description": "Which tree traversal technique guarantees visiting nodes level by level (breadth-first traversal) starting from the root of a binary tree?",
        "constraints": "0 <= node_count <= 10^4",
        "input_format": "Level-order traversal list with null for empty nodes.",
        "output_format": "Integer depth.",
        "examples": [{"input": "3 9 20 null null 15 7", "output": "3", "explanation": "Maximum depth is 3."}],
        "starter_code": {"python": "def solve(nodes: list[str]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. In-order traversal", "B. Pre-order traversal", "C. Post-order traversal", "D. Level-order (BFS) traversal"],
        "diagnostic_correct_option": "D",
        "options": ["A. In-order traversal", "B. Pre-order traversal", "C. Post-order traversal", "D. Level-order (BFS) traversal"],
        "correct_option": "D",
        "test_cases": [
            {"input": "3 9 20 null null 15 7", "expected_output": "3", "is_hidden": False},
            {"input": "1 null 2", "expected_output": "2", "is_hidden": True},
        ]
    },
    {
        "topic": "Trees",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Validate Binary Search Tree",
        "slug": "validate-binary-search-tree",
        "description": "Given the root of a binary tree, determine if it is a valid binary search tree (BST).",
        "constraints": "1 <= node_count <= 10^4",
        "input_format": "Level-order representation.",
        "output_format": "true or false",
        "examples": [{"input": "2 1 3", "output": "true", "explanation": "Valid BST."}],
        "starter_code": {"python": "def solve(nodes: list[str]) -> bool:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "2 1 3", "expected_output": "true", "is_hidden": False},
            {"input": "5 1 4 null null 3 6", "expected_output": "false", "is_hidden": True},
        ]
    },
    {
        "topic": "Trees",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Binary Tree Maximum Path Sum",
        "slug": "binary-tree-maximum-path-sum",
        "description": "A path in a binary tree is a sequence of nodes where each pair of adjacent nodes has an edge. Return max path sum.",
        "constraints": "1 <= node_count <= 3 * 10^4",
        "input_format": "Level-order representation.",
        "output_format": "Maximum path sum integer.",
        "examples": [{"input": "-10 9 20 null null 15 7", "output": "42", "explanation": "Optimal path is 15 -> 20 -> 7 sum 42."}],
        "starter_code": {"python": "def solve(nodes: list[str]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "-10 9 20 null null 15 7", "expected_output": "42", "is_hidden": False},
            {"input": "1 2 3", "expected_output": "6", "is_hidden": True},
        ]
    },

    # 10. Graphs
    {
        "topic": "Graphs",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Find Center of Star Graph",
        "slug": "find-center-of-star-graph",
        "description": "In a star graph with N nodes, how can the center node be identified directly from the edges?",
        "constraints": "3 <= n <= 10^5",
        "input_format": "Line 1: integer `n`. Line 2..n: edge pairs `u v`.",
        "output_format": "Center node integer.",
        "examples": [{"input": "4\n1 2\n2 3\n4 2", "output": "2", "explanation": "Node 2 is connected to all other nodes."}],
        "starter_code": {"python": "def solve(n: int, edges: list[list[int]]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "is_diagnostic": True,
        "question_type": "MCQ",
        "diagnostic_options": ["A. It has degree 1", "B. It has degree N-1", "C. It has degree N", "D. It has degree N/2"],
        "diagnostic_correct_option": "B",
        "options": ["A. It has degree 1", "B. It has degree N-1", "C. It has degree N", "D. It has degree N/2"],
        "correct_option": "B",
        "test_cases": [
            {"input": "4\n1 2\n2 3\n4 2", "expected_output": "2", "is_hidden": False},
            {"input": "5\n1 2\n5 1\n1 3\n1 4", "expected_output": "1", "is_hidden": True},
        ]
    },
    {
        "topic": "Graphs",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Number of Connected Islands",
        "slug": "number-of-connected-islands",
        "description": "Given an m x n 2D binary grid of '1's (land) and '0's (water), return the total number of connected islands.",
        "constraints": "1 <= m, n <= 300",
        "input_format": "Line 1: `m n`. Line 2..m+1: grid rows.",
        "output_format": "Number of islands integer.",
        "examples": [{"input": "4 5\n11110\n11010\n11000\n00000", "output": "1", "explanation": "Single connected island."}],
        "starter_code": {"python": "def solve(grid: list[list[str]]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "4 5\n11110\n11010\n11000\n00000", "expected_output": "1", "is_hidden": False},
            {"input": "4 5\n11000\n11000\n00100\n00011", "expected_output": "3", "is_hidden": True},
        ]
    },
    {
        "topic": "Graphs",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Word Ladder Shortest Transformation",
        "slug": "word-ladder-shortest-transformation",
        "description": "Given beginWord, endWord, and wordList, return length of shortest transformation sequence from beginWord to endWord.",
        "constraints": "1 <= wordList.length <= 5000",
        "input_format": "Line 1: `beginWord`. Line 2: `endWord`. Line 3: space-separated `wordList`.",
        "output_format": "Sequence length integer or 0.",
        "examples": [{"input": "hit\ncog\nhot dot dog lot log cog", "output": "5", "explanation": "hit -> hot -> dot -> dog -> cog (length 5)"}],
        "starter_code": {"python": "def solve(begin: str, end: str, words: list[str]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "hit\ncog\nhot dot dog lot log cog", "expected_output": "5", "is_hidden": False},
            {"input": "hit\ncog\nhot dot dog lot log", "expected_output": "0", "is_hidden": True},
        ]
    },

    # 11. Greedy
    {
        "topic": "Greedy",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Assign Cookies to Children",
        "slug": "assign-cookies-to-children",
        "description": "Maximize number of content children given greed factor array `g` and cookie size array `s`.",
        "constraints": "1 <= g.length, s.length <= 3 * 10^4",
        "input_format": "Line 1: `g`. Line 2: `s`.",
        "output_format": "Integer count of content children.",
        "examples": [{"input": "1 2 3\n1 1", "output": "1", "explanation": "Only 1 child can be satisfied."}],
        "starter_code": {"python": "def solve(g: list[int], s: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 2 3\n1 1", "expected_output": "1", "is_hidden": False},
            {"input": "1 2\n1 2 3", "expected_output": "2", "is_hidden": True},
        ]
    },
    {
        "topic": "Greedy",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Jump Game Reachability",
        "slug": "jump-game-reachability",
        "description": "Given an integer array `nums` where each element represents max jump length, return true if you can reach the last index.",
        "constraints": "1 <= nums.length <= 10^4",
        "input_format": "Space separated integers.",
        "output_format": "true or false",
        "examples": [{"input": "2 3 1 1 4", "output": "true", "explanation": "Jump 1 step from index 0 to 1, then 3 steps to end."}],
        "starter_code": {"python": "def solve(nums: list[int]) -> bool:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "2 3 1 1 4", "expected_output": "true", "is_hidden": False},
            {"input": "3 2 1 0 4", "expected_output": "false", "is_hidden": True},
        ]
    },
    {
        "topic": "Greedy",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Candy Distribution Problem",
        "slug": "candy-distribution-problem",
        "description": "There are n children in a line with ratings. Give minimum total candies such that higher rated child gets more than neighbors.",
        "constraints": "1 <= ratings.length <= 2 * 10^4",
        "input_format": "Space separated ratings.",
        "output_format": "Minimum total candies integer.",
        "examples": [{"input": "1 0 2", "output": "5", "explanation": "Candies given: [2, 1, 2] sum = 5."}],
        "starter_code": {"python": "def solve(ratings: list[int]) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 0 2", "expected_output": "5", "is_hidden": False},
            {"input": "1 2 2", "expected_output": "4", "is_hidden": True},
        ]
    },

    # 12. Dynamic Programming
    {
        "topic": "Dynamic Programming",
        "difficulty": ProblemDifficulty.EASY,
        "title": "Climbing Stairs Ways",
        "slug": "climbing-stairs-ways",
        "description": "You are climbing a staircase with `n` steps. Each time you can climb 1 or 2 steps. How many distinct ways can you reach top?",
        "constraints": "1 <= n <= 45",
        "input_format": "Integer `n`.",
        "output_format": "Integer count of ways.",
        "examples": [{"input": "3", "output": "3", "explanation": "1+1+1, 1+2, 2+1 (3 ways)"}],
        "starter_code": {"python": "def solve(n: int) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "3", "expected_output": "3", "is_hidden": False},
            {"input": "5", "expected_output": "8", "is_hidden": True},
        ]
    },
    {
        "topic": "Dynamic Programming",
        "difficulty": ProblemDifficulty.MEDIUM,
        "title": "Coin Change Minimum Coins",
        "slug": "coin-change-minimum-coins",
        "description": "Given an integer array `coins` and total `amount`, return fewest number of coins needed to make up amount or -1.",
        "constraints": "1 <= coins.length <= 12\n0 <= amount <= 10^4",
        "input_format": "Line 1: space separated coins. Line 2: amount.",
        "output_format": "Minimum coins integer or -1.",
        "examples": [{"input": "1 2 5\n11", "output": "3", "explanation": "11 = 5 + 5 + 1 (3 coins)"}],
        "starter_code": {"python": "def solve(coins: list[int], amount: int) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "1 2 5\n11", "expected_output": "3", "is_hidden": False},
            {"input": "2\n3", "expected_output": "-1", "is_hidden": True},
        ]
    },
    {
        "topic": "Dynamic Programming",
        "difficulty": ProblemDifficulty.HARD,
        "title": "Edit Distance Levenshtein",
        "slug": "edit-distance-levenshtein",
        "description": "Given two strings `word1` and `word2`, return minimum operations (insert, delete, replace) to convert `word1` to `word2`.",
        "constraints": "0 <= word1.length, word2.length <= 500",
        "input_format": "Line 1: `word1`. Line 2: `word2`.",
        "output_format": "Minimum edit distance integer.",
        "examples": [{"input": "horse\nros", "output": "3", "explanation": "horse -> rorse -> rose -> ros (3 ops)"}],
        "starter_code": {"python": "def solve(w1: str, w2: str) -> int:\n    pass"},
        "solution_language_support": ["python", "cpp"],
        "test_cases": [
            {"input": "horse\nros", "expected_output": "3", "is_hidden": False},
            {"input": "intention\nexecution", "expected_output": "5", "is_hidden": True},
        ]
    },
]


async def _seed_with_session(session):
    print("Starting CodeArena Module 3 data seeding...")

    # 1. Seed Topics
    topic_map = {}
    for t_data in TOPICS_SEED_DATA:
        stmt = select(Topic).where(Topic.name == t_data["name"])
        result = await session.execute(stmt)
        existing_topic = result.scalar_one_or_none()

        if not existing_topic:
            new_topic = Topic(name=t_data["name"], description=t_data["description"])
            session.add(new_topic)
            await session.flush()
            topic_map[t_data["name"]] = new_topic
            print(f"Created topic: '{t_data['name']}'")
        else:
            topic_map[t_data["name"]] = existing_topic

    await session.commit()

    # 2. Seed Problems, ProblemTopic, and Test Cases
    problems_created = 0
    for p_data in PROBLEMS_SEED_DATA:
        stmt = select(Problem).where(Problem.slug == p_data["slug"])
        result = await session.execute(stmt)
        existing_problem = result.scalar_one_or_none()

        if not existing_problem:
            new_problem = Problem(
                title=p_data["title"],
                slug=p_data["slug"],
                description=p_data["description"],
                difficulty=p_data["difficulty"],
                constraints=p_data.get("constraints"),
                input_format=p_data.get("input_format"),
                output_format=p_data.get("output_format"),
                examples=p_data.get("examples"),
                starter_code=p_data.get("starter_code"),
                solution_language_support=p_data.get("solution_language_support"),
                is_diagnostic=p_data.get("is_diagnostic", False),
                diagnostic_options=p_data.get("diagnostic_options"),
                diagnostic_correct_option=p_data.get("diagnostic_correct_option"),
                question_type=p_data.get("question_type", "CODING"),
                options=p_data.get("diagnostic_options") or p_data.get("options"),
                correct_option=p_data.get("diagnostic_correct_option") or p_data.get("correct_option"),
            )
            session.add(new_problem)
            await session.flush()
            problem_obj = new_problem
            problems_created += 1
            print(f"Created problem: '{p_data['title']}' [{p_data['difficulty'].value}]")
        else:
            problem_obj = existing_problem
            existing_problem.description = p_data["description"]
            existing_problem.is_diagnostic = p_data.get("is_diagnostic", False)
            existing_problem.diagnostic_options = p_data.get("diagnostic_options")
            existing_problem.diagnostic_correct_option = p_data.get("diagnostic_correct_option")
            existing_problem.question_type = p_data.get("question_type", "CODING")
            existing_problem.options = p_data.get("diagnostic_options") or p_data.get("options")
            existing_problem.correct_option = p_data.get("diagnostic_correct_option") or p_data.get("correct_option")

        # Link Topic via ProblemTopic junction
        topic_name = p_data["topic"]
        topic_obj = topic_map.get(topic_name)
        if topic_obj:
            pt_stmt = select(ProblemTopic).where(
                ProblemTopic.problem_id == problem_obj.id,
                ProblemTopic.topic_id == topic_obj.id,
            )
            pt_result = await session.execute(pt_stmt)
            if not pt_result.scalar_one_or_none():
                session.add(ProblemTopic(problem_id=problem_obj.id, topic_id=topic_obj.id))

        # Seed Test Cases
        for tc_data in p_data.get("test_cases", []):
            tc_stmt = select(TestCase).where(
                TestCase.problem_id == problem_obj.id,
                TestCase.input == tc_data["input"],
                TestCase.expected_output == tc_data["expected_output"],
            )
            tc_result = await session.execute(tc_stmt)
            if not tc_result.scalar_one_or_none():
                session.add(
                    TestCase(
                        problem_id=problem_obj.id,
                        input=tc_data["input"],
                        expected_output=tc_data["expected_output"],
                        is_hidden=tc_data.get("is_hidden", False),
                    )
                )

    await session.commit()
    print(f"Seeding completed successfully! Total created: {problems_created} new problems.")


async def seed_data(session=None):
    """Seed 12 topics, 36 problems, problem_topic junction rows, and test cases deterministically."""
    if session is not None:
        await _seed_with_session(session)
    else:
        async with AsyncSessionLocal() as db_session:
            await _seed_with_session(db_session)



if __name__ == "__main__":
    asyncio.run(seed_data())
