##################################################################################################
# testing the python agent:
# from agents.python_agent import python_agent

# print(
#     python_agent(
#         "Generate and save 3 QR codes pointing to https://www.udemy.com/course/langchain"
#     )
# )
##################################################################################################


##################################################################################################
# testing the csv agent:
from agents.csv_agent import csv_agent

# Load CSV file as bytes
with open("test.csv", "rb") as f:
    csv_bytes = f.read()

csv_filename = "test.csv"

# Ask the agent to summarize the CSV
# result = csv_agent(
#     user_input="Load the CSV and summarize it",
#     csv_bytes=csv_bytes,
#     csv_filename=csv_filename
# )
# print(result)

# Test file generation
result = csv_agent(
    user_input="Load the CSV, compute df.describe(), and save it as summary.csv",
    csv_bytes=csv_bytes,
    csv_filename=csv_filename
)
print(result)
##################################################################################################
