# Excel File Format for MCQ Quiz

Your Excel file should follow this structure for the application to work correctly:

## Required Columns

| Column 1 | Column 2                       | Column 3 | Column 4 |
| -------- | ------------------------------ | -------- | -------- |
| Question | What is the capital of France? |          |          |
| A        | London                         |          |          |
| B        | Paris                          |          | A        |
| C        | Berlin                         |          |          |
| D        | Madrid                         |          |          |

## Format Rules

1. **Question Row**: Start with "Question" in Column 1, question text in Column 2
2. **Choice Rows**: Use A, B, C, D in Column 1, choice text in Column 2
3. **Answer Indicator**: Put the correct choice letter in Column 4 (e.g., "A" for choice A)
4. **Empty Rows**: Column 3 can be left empty
5. **Multiple Tables**: You can have multiple tables separated by "Table 1", "Table 2", etc.

## Example Structure

```
Question    | What is 2 + 2?           |           |
A           | 3                         |           |
B           | 4                         |           | B
C           | 5                         |           |
D           | 6                         |           |

Question    | What color is the sky?    |           |
A           | Red                       |           |
B           | Green                     |           |
C           | Blue                      |           | C
D           | Yellow                    |           |
```

## Tips

- Make sure all choices (A, B, C, D) are present for each question
- The answer indicator in Column 4 must match one of the choice letters
- You can have as many questions as you want
- The application will automatically detect the structure
