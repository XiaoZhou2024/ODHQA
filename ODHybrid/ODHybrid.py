import json
from dotenv import dotenv_values
from config.prompt_config import *
from tools.expression_calculator import *
from tools.operations_utils import *
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_community.retrievers import BM25Retriever

# ----------------------------- Environment & Model Loading -----------------------------
llm_env = dotenv_values("../.env")

dataset_filepath = "../dataset/test_dataset.json"
output_filepath = "./results.json"

llm = ChatOpenAI(
    model="qwen25-72b",
    base_url=llm_env["LLM_BASE_URL"],
    api_key=llm_env["LLM_API_SECRET_KEY"]
)

# ----------------------- Dataset Loading -----------------------
with open(dataset_filepath, encoding="utf-8") as f:
    dataset = json.load(f)

# ----------------------- Document and Retriever Construction -----------------------
documents = []
for item in dataset:
    doc = Document(page_content=item["document_title"], metadata={"uid": item["uid"]})
    if doc not in documents:
        documents.append(doc)

retriever = BM25Retriever.from_documents(documents, k=1)


# ----------------------- Utility Functions -----------------------
def get_id_index(uid, data_list):
    """
    Returns the index of the element with the specified uid in data_list.

    Args:
        uid (str): The unique identifier to search for.
        data_list (List[dict]): List of data entries.

    Returns:
        int: Index of the element if found, -1 otherwise.
    """
    for i, data in enumerate(data_list):
        if data['uid'] == uid:
            return i
    return -1

def get_retriever_data(docs):
    """
    Extracts relevant table, content, title, and table title from retrieved documents.

    Args:
        docs (List[Document]): List of retrieved documents.

    Returns:
        Tuple: Tables, content, document title, table titles.
    """
    uid = docs[0].metadata["uid"]
    id_index = get_id_index(uid, dataset)
    entry = dataset[id_index]
    return entry["tables"], entry["content"], entry["document_title"], entry["table_title"]


# ----------------------- Prompt and Chain Construction -----------------------
extract_prompt = PromptTemplate.from_template(extract_template)
extract_chain = extract_prompt | llm

get_sub_table_prompt = PromptTemplate.from_template(get_sub_table_template)
get_sub_table_chain = get_sub_table_prompt | llm

get_sub_content_prompt = PromptTemplate.from_template(get_sub_content_template)
get_sub_content_chain = get_sub_content_prompt | llm

sub_arith_prog_prompt = PromptTemplate.from_template(sub_evidence_to_arithmetic_program_template)
sub_arith_prog_chain = sub_arith_prog_prompt | llm

span_selection_prompt = PromptTemplate.from_template(sub_evidence_to_span_selection_template)
span_selection_chain = span_selection_prompt | llm


# ------------------------ Main Processing Function ------------------------
def main():
    retrieval_cnt = 0
    for index, data in enumerate(dataset):

        document_title = data["document_title"]
        question = data["qa"]["question"]
        answer = data["qa"]["answer"]
        predicted_label = data["qa"]["question_type"]
        ground_truth_program = data["qa"].get("program", None) if predicted_label == "arithmetic" else None

        # Extract key information from the question using the LLM chain
        key_information = extract_chain.invoke({"question": question}).content
        print(key_information)
        print(document_title)

        # Retrieve relevant tables, content, and metadata
        retrieved_results = retriever.invoke(key_information)
        retriever_table, retriever_content, retriever_document_title, retriever_table_titles = get_retriever_data(retrieved_results)
        tables = combine_tables_with_titles(retriever_table, retriever_table_titles)

        # Extract pertinent sub-table using the LLM chain
        sub_table_reasoning = get_sub_table_chain.invoke({"query": question, "table": tables}).content
        print(sub_table_reasoning, '\n')
        print("******************* Sub Table **********************")
        sub_table = extract_sub_table(sub_table_reasoning)
        print(sub_table)
        print("***************************************************")

        # Extract pertinent text context using the LLM chain
        sub_content_reasoning = get_sub_content_chain.invoke({"query": question, "content": retriever_content}).content
        print(sub_content_reasoning, '\n')
        print("******************* Sub Content *******************")
        sub_content = extract_sub_content(sub_content_reasoning)
        print(sub_content)
        print("***************************************************")

        inference_reasoning, predicted_program, llm_answer = "", None, None

        # Handle arithmetic questions
        if predicted_label == "arithmetic":
            inference_reasoning = sub_arith_prog_chain.invoke({
                "sub_table": sub_table,
                "sub_content": sub_content,
                "query": question
            }).content
            print(inference_reasoning, '\n')
            print("----------------- Program ------------------------")
            predicted_program = extract_predicted_program(inference_reasoning)
            print(f"Predicted program: {predicted_program}")
            print(f"Ground truth program: {ground_truth_program}")
            predicted_program = remove_multiply_suffix(str(predicted_program))
            print(f"Predicted program (suffix removed): {predicted_program}")
            llm_answer = evaluate_expression([str(predicted_program)])
            print(f"Predicted Answer: {llm_answer}")
            print(f"Standard Answer: {answer}")
            print("------------------------------------------------")

        # Handle span-selection type questions
        elif predicted_label == "span_selection":
            inference_reasoning = span_selection_chain.invoke({
                "sub_table": sub_table,
                "sub_content": sub_content,
                "query": question
            }).content
            print(inference_reasoning, '\n')
            print("----------------- Answer ------------------------")
            llm_answer = extract_sub_answer(inference_reasoning)
            print(f"Predicted Answer: {llm_answer}")
            print(f"Standard Answer: {answer}")
            print("------------------------------------------------")

        # Store output of the current instance
        new_data = {
            "index": index,
            "question": question,
            "sub_table_reasoning": sub_table_reasoning,
            "sub_content_reasoning": sub_content_reasoning,
            "inference_reasoning": inference_reasoning,
            "ground_truth_program": ground_truth_program,
            "predicted_program": predicted_program,
            "answer": answer,
            "llm_answer": llm_answer,
            "question_type": predicted_label,
        }

        if document_title in retriever_document_title:
            retrieval_cnt += 1
            print(f"Successful retrieval count: {retrieval_cnt}")

        append_to_json_file(output_filepath, new_data)


if __name__ == "__main__":
    main()