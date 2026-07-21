'''
Local workspace for teachers to input their confidential students




Research:

- How can Flet access Gemma 4 local AI model.

--> Ollama gives your Python app a simple localhost HTTP API
-->



- What does this mean for the inputted documents, and how gemma 4 cannot access local folders and documents

- flet should show the different generated folders
- that also makes me wonder how gemma's output will be parsed and separated.



- can the outputted documents be put in folders that exist in Flet as well as the system? This would be easier for teacher's workflow


todo: install gemma
todo: connect flet to gemma and docling.
todo: input a hello world document -- make it a PDF -- Docling should parse and output an MD file.
todo: ****** HOW TO FEED IN A FILE TO GEMMA ******
todo: user will enter a prompt through flet, and gemma should respond (Try to make this output reappear on the Flet UI)

** Ollama is a free, open-source application that allows to download and run AI models like Gemma 4 directly on your computer
--> It is a light-weight engine and wrapper, that automates teh tasks needed in order to run an AI model
--> these tasks include formatting, memory management, and server setup, so that you can run the model completely offline (locally :) )







How will accessing files created by Docling and named by Flet be accessed by Gemma?
Can we input any files into Gemma? How? How can I make it access only the specific Gemma folders?


--> Short answer: Ollama's REST API.

'''

import flet as ft

from pathlib import Path
from docling.document_converter import DocumentConverter

#--> difference b.t 'chat' and 'asynchat'?
from ollama import chat

#this function will be called, and will operate on a file that was chosen from flet UI
def user_inputs_doc(selected_file: str):


    # initialize the document converter object:
    converter = DocumentConverter()

    # convert a lab assignment --> this outputs a "dcoling document" that can be parsed and converted into different file formats.
    conversion_result = converter.convert(selected_file)

    # convert this docling document to a markdown file:
    markdown_file = conversion_result.document.export_to_markdown()

    # The way it works:
    # You convert your markdown to a string, and you input that string in
    # your message to Gemma as one of its 'message' parameters

    response = chat(

        # --> Check the way 4b is named on your system!
        model="gemma4:e4b-it-q8_0 ",
        messages=[
            {
                "role": "user",
                "content": f"""Read the following extracted document, and give me steps on how to
                                complete this assignment:


                            DOCUMENT:
                            {markdown_file}"""
            }
        ]
    )

    print(response.message.content)











#a basic UI:
#--> flet has a built-in document insertion object.

#a flet Page is a UI window
def main(page: ft.Page):
    page.window.width = 700
    page.window.height = 500




    #for document insertion, first define a callback handler:
    def file_picker_result (e):

        # e.files will check for metadata of file, to ensure user inputted something valid
        if e.files:

            ##since we have allow_multiple=False, we only access the first file of this FilePickerResult list
            selected_file = e.files[0]

            #call our function above.
            user_inputs_doc(selected_file)


        else:
            print("No document entered")

    #create a file picker object:
    file_picker = ft.FilePicker()
    file_picker.on_result = file_picker_result

    page.services.append(file_picker)


    #allow for the file explorer dialog, by pressing a button
    #when it is pressed, the file_picker object will be triggered, then when a file is chosen,
    #'on_result' will call the file_picker result function, which calls the docling, and gemma function (first one)
    async def upload_document_clicked(e):
        files = await file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=['pdf', 'doc', 'docx']
        )

        if files:

            #this is a string path
            selected_file_path = files[0].path



            user_inputs_doc(selected_file_path)
        else:
            print("No document entered")

    page.add(
        ft.Button(""
                  "Upload Document",
                  on_click=upload_document_clicked)
    )

#mandatory line, for program to run your flet application:
ft.app(target=main)

