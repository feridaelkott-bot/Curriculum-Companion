'''
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

'''
Application Flow:
1. Show a welcome screen.
2. Let the teacher select one curriculum document.
3. Convert the document to Markdown with Docling
4. Send the extracted Markdown to a local FGemma model through Ollama
5. Display the generated activities
6. Save the generated activities as a Markdown file
'''

#------------------------------------------------------
# IMPORTS
#------------------------------------------------------

import flet as ft

from pathlib import Path
from docling.document_converter import DocumentConverter

#--> difference b.t 'chat' and 'asynchat'?
from ollama import ResponseError, chat

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
        # gemma4:e2b
        # --> Check the way 4b is named on your system!
        model="gemma4:12b",
        messages=[
            {
                "role": "user",
                "content": f"""
                                    Below is the Markdown content extracted from a curriculum document:
                                    
                                    ---
                                    {markdown_file}
                                    ---
                                    
                                    ### STRICT AI INSTRUCTIONS:
                                    You are an expert curriculum assistant. 
                                    
                                    DO NOT summarize assessment rules, grading levels, or administrative guidelines. Focus ONLY on the learning content.
                                    
                                    Identify EVERY distinct curriculum "Strand" in the text above (e.g., Strand B: Life Systems, Strand C: Matter & Energy, Strand D: Structures, Strand E: Earth & Space). 
                                    
                                    FOR EACH STRAND identified in the document, you must generate 5 distinct, highly engaging student activities to solidify learning expectations.
                                    
                                    ### MANDATORY REQUIREMENTS PER STRAND:
                                    - Activity 1: MUST be a Local Field Trip / Community Excursion
                                    - Activity 2: MUST be an Interactive Group Activity
                                    - Activity 3: MUST be an Interactive Group Activity
                                    - Activity 4: Hands-On / Experiential Activity
                                    - Activity 5: Applied STEM / Design Challenge
                                    
                                    ---
                                    
                                    ### OUTPUT FORMAT (Repeat this full block for EVERY strand found):
                                    
                                    # Strand: [Insert Strand Name/Letter]
                                    
                                    ## Activity 1: [Field Trip Name]
                                    - **Activity Type:** Field Trip / Excursion
                                    - **Target Strand Expectation:** [Specific concept from this strand]
                                    - **Description:** [3 sentences explaining what students will do]
                                    - **Why It Solidifies Understanding:** [2 sentences explaining why this cements the strand concept]
                                    
                                    ## Activity 2: [Group Activity Name]
                                    - **Activity Type:** Group Activity
                                    - **Target Strand Expectation:** [Specific concept from this strand]
                                    - **Description:** [3 sentences explaining what student groups will do]
                                    - **Why It Solidifies Understanding:** [2 sentences explaining why this cements the strand concept]
                                    
                                    ## Activity 3: [Group Activity Name]
                                    - **Activity Type:** Group Activity
                                    - **Target Strand Expectation:** [Specific concept from this strand]
                                    - **Description:** [3 sentences explaining what student groups will do]
                                    - **Why It Solidifies Understanding:** [2 sentences explaining why this cements the strand concept]
                                    
                                    ## Activity 4: [Activity Name]
                                    - **Activity Type:** Hands-On Experiential
                                    - **Target Strand Expectation:** [Specific concept from this strand]
                                    - **Description:** [3 sentences explaining the procedure]
                                    - **Why It Solidifies Understanding:** [2 sentences explaining why this cements the strand concept]
                                    
                                    ## Activity 5: [Activity Name]
                                    - **Activity Type:** STEM / Design Challenge
                                    - **Target Strand Expectation:** [Specific concept from this strand]
                                    - **Description:** [3 sentences explaining the procedure]
                                    - **Why It Solidifies Understanding:** [2 sentences explaining why this cements the strand concept]
                                    
                                    ---
                                    
                                    Begin immediately with your first strand. Do not write any introduction.
                                """
            }
        ]
    )

    print(response.message.content)


'''We have 7 units, EACH IS ITS OWN pdf FILE.

We will use Docling to convert each of these PDF files to a Markdown file, that will be given to Gemma as text for it to generate responses from. 


For each unit, I want Gemma to generate a FILE for activities that the teacher can plan for their students.



--> For EACH of the seven units, generate a file/response of 5 different activities, including field trips, and other fun group activities that a teacher can rely on to solidify curriculum expectations in their class. 
--> For each activity generated, include a reason why it would be a good way to solidify understanding of that unit. 
--> Gemma produces a complete text response for each prompt it is given. 
--> This means that the response I am given FOR EACH of the seven units files, I generate a corresponding activities markdown file for it

Then these files will be saved in the teacher's OS, in /home/activities_folder/[all docs], 


FOR TOMORROW: 
Try to make these files visible on the UI. If not, the UI should output a message regarding where the files exist on the user's computer. 

'''











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

