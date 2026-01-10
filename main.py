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
# # testing the csv agent:
# from agents.csv_agent import csv_agent

# # Load CSV file as bytes
# with open("test.csv", "rb") as f:
#     csv_bytes = f.read()

# csv_filename = "test.csv"
##---------------------------------------------------------------------------------------------------
# # Ask the agent to summarize the CSV
# # result = csv_agent(
# #     user_input="Load the CSV and summarize it",
# #     csv_bytes=csv_bytes,
# #     csv_filename=csv_filename
# # )
# # print(result)
##---------------------------------------------------------------------------------------------------
# # Test file generation
# result = csv_agent(
#     user_input="Load the CSV, compute df.describe(), and save it as summary.csv",
#     csv_bytes=csv_bytes,
#     csv_filename=csv_filename
# )
# print(result)
##################################################################################################

##################################################################################################
# testing the controller:
# Controller with NO file (should route to Python agent)
from agents.controller import CodeInterpreterController

controller = CodeInterpreterController()

##---------------------------------------------------------------------------------------------------
# result = controller.run(
#     user_input="print('Hello from Python agent')"
# )

# print("LOGS:\n", result.logs)
# print("FILES:\n", result.files)
##---------------------------------------------------------------------------------------------------
# # Load a sample CSV
# # Controller with a CSV file (should route to CSV agent)
# with open("test.csv", "rb") as f:
#     csv_bytes = f.read()

# result = controller.run(
#     user_input="Load the CSV and save df.describe() as summary.csv",
#     file_bytes=csv_bytes,
#     filename="test.csv"
# )

# print("LOGS:\n", result.logs)
# print("FILES:\n", result.files)
##---------------------------------------------------------------------------------------------------
# # Controller with a non‑CSV file (should route to Python agent)
# fake_file_bytes = b"hello world"

# result = controller.run(
#     user_input="print('This should go to python agent')",
#     file_bytes=fake_file_bytes,
#     filename="notes.txt"
# )

# print("LOGS:\n", result.logs)
# print("FILES:\n", result.files)
##---------------------------------------------------------------------------------------------------
# Controller response structure
response = controller.run("1+1")

print(type(response))
print(response.logs[:200])
print(response.files)
##################################################################################################
