from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import UserDataForm, UploadCSVForm
from .models import UserData, Feedback, ToolResult
import joblib
from .helpers import prepare_input_data
import numpy as np
from django.contrib.auth.decorators import login_required
import subprocess
import json
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os
import re
from ansi2html import Ansi2HTMLConverter
import pandas as pd 
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

def load_model():
    print("Executing load_model function")
    try:
        with open('svmxss.pkl', 'rb') as f:
            model = joblib.load(f)
    except FileNotFoundError:
        model = retrain_model()
    print("Finished executing load_model function")
    return model

def retrain_model():
    print("Executing retrain_model function")
    data = UserData.objects.all()
    if not data:
        print("Finished executing retrain_model function with no data")
        return None

    X = [[d.goal, d.attackT, d.skill, d.automation, d.platform] for d in data]
    y = [d.suggest for d in data]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = SVC()
    model.fit(X_train, y_train)
    
    with open('svmxss.pkl', 'wb') as f:
        joblib.dump(model, f)
    
    print("Finished executing retrain_model function")
    return model

def delete_data(request, data_id):
    print("Executing delete_data function")
    data_to_delete = get_object_or_404(UserData, pk=data_id)
    if data_to_delete.user == request.user:
        data_to_delete.delete()
        print("Finished executing delete_data function successfully")
        return redirect('view_data')
    else:
        print("Finished executing delete_data function with forbidden error")
        return HttpResponseForbidden("You are not allowed to delete this asset.")

@login_required
def new_data(request):
    print("Executing new_data function")
    if request.method == 'POST':
        form = UserDataForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data['goal']
            attackT = form.cleaned_data['attackT']
            skill = form.cleaned_data['skill']
            automation = form.cleaned_data['automation']
            platform = form.cleaned_data['platform']
            
            print(f"User choice - Goal: {goal}, Attack Type: {attackT}, Skill: {skill}, Automation: {automation}, Platform: {platform}")
            
            input_data = prepare_input_data(goal, attackT, skill, automation, platform)
            
            # Tambahkan nama fitur pada input_data menggunakan pandas
            feature_names = ['goal', 'attackT', 'skill', 'automation', 'platform']
            input_df = pd.DataFrame(input_data, columns=feature_names)
            
            svm_model = load_model()
            prediction = svm_model.predict(input_df)[0]
            print(f"Prediction: {prediction}")
            
            UserData.objects.create(
                user=request.user, 
                goal=goal, 
                attackT=attackT, 
                skill=skill, 
                automation=automation, 
                platform=platform, 
                suggest=prediction
            )
            return redirect('success')  
    else:
        form = UserDataForm()
    print("Finished executing new_data function")
    return render(request, 'suggestxss/new_data.html', {'form': form})

def success(request):
    print("Executing success function")
    return render(request, 'suggestxss/success.html')
    print("Finished executing success function")

def result(request):
    print("Executing result function")
    data = UserData.objects.filter(user=request.user).last()
    feedback = Feedback.objects.filter(user_data=data).last() if data else None
    print("Finished executing result function")
    return render(request, 'suggestxss/result.html', {'data': data})

def home(request):
    print("Executing home function")
    return render(request, 'suggestxss/home.html')
    print("Finished executing home function")

def user_login(request):
    print("Executing user_login function")
    login_error = False  # Initialize login error flag
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print("Finished executing user_login function successfully")
            return redirect('dashboard')
        else:
            login_error = True
            print("Finished executing user_login function with error")
    else:
        print("Finished executing user_login function")
    return render(request, 'suggestxss/login.html', {'login_error': login_error})


def user_register(request):
    print("Executing user_register function")
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        print("Finished executing user_register function successfully")
        return redirect('dashboard')
    print("Finished executing user_register function")
    return render(request, 'suggestxss/register.html')

@login_required
def view_data(request):
    print("Executing view_data function")
    data = UserData.objects.filter(user=request.user).order_by('-created_at')
    print("Finished executing view_data function")
    return render(request, 'suggestxss/view_data.html', {'data': data})

@login_required
def dashboard(request):
    print("Executing dashboard function")
    print("Finished executing dashboard function")
    return render(request, 'suggestxss/dashboard.html')

@login_required
def nmap_tool(request):
    print("Executing nmap_tool function")
    if request.method == 'POST':
        target = request.POST.get('target')
        if target:
            result = subprocess.run(['nmap', target], capture_output=True, text=True)
            output = result.stdout
            ToolResult.objects.create(user=request.user, tool_name='Nmap', target=target, result=output)
        else:
            output = "No target specified."
    else:
        output = None
    print("Finished executing nmap_tool function")
    return render(request, 'suggestxss/nmap_tool.html', {'output': output})

def remove_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'''
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by a control sequence
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    ''', re.VERBOSE)
    return ansi_escape.sub('', text)

@csrf_exempt
def run_xsstrike(request):
    print("Executing run_xsstrike function")
    if request.method == 'POST':
        url = request.POST.get('url', '')
        if not url:
            print("Finished executing run_xsstrike function with error: No URL provided")
            return render(request, 'suggestxss/run_xsstrike.html', {'error': 'No URL provided'})

        try:
            result = subprocess.run(
                ['python3', os.path.expanduser('~/XSStrike/xsstrike.py'), '-u', url, '--crawl'],
                capture_output=True, text=True, check=True
            )
            output = remove_ansi_escape_sequences(result.stdout)
            ToolResult.objects.create(user=request.user, tool_name='XSStrike', target=url, result=output)
        except subprocess.CalledProcessError as e:
            print(f"Finished executing run_xsstrike function with error: {str(e)}")
            return render(request, 'suggestxss/run_xsstrike.html', {'error': str(e)})
        print("Finished executing run_xsstrike function successfully")
        return render(request, 'suggestxss/run_xsstrike.html', {'output': output})

    print("Finished executing run_xsstrike function")
    return render(request, 'suggestxss/run_xsstrike.html')

@csrf_exempt
def run_pwnxss(request):
    print("Executing run_pwnxss function")
    if request.method == 'POST':
        url = request.POST.get('url', '')
        if not url:
            print("Finished executing run_pwnxss function with error: No URL provided")
            return render(request, 'suggestxss/run_pwnxss.html',{'error': 'No URL provided'})

        try:
            result = subprocess.run(
                ['python3', os.path.expanduser('~/PwnXSS/pwnxss.py'), '--single', url],
                capture_output=True, text=True, check=True
            )
            output = result.stdout
            start_marker = "Checking connection to:"
            if start_marker in output:
                output = output[output.index(start_marker):]
            conv = Ansi2HTMLConverter()
            html_output = conv.convert(output, full=False)
            ToolResult.objects.create(user=request.user, tool_name='PwnXSS', target=url, result=html_output)
        except subprocess.CalledProcessError as e:
            print(f"Finished executing run_pwnxss function with error: {str(e)}")
            return render(request, 'suggestxss/run_pwnxss.html', {'error': str(e)})
        print("Finished executing run_pwnxss function successfully")
        return render(request, 'suggestxss/run_pwnxss.html', {'output': html_output})

    print("Finished executing run_pwnxss function")
    return render(request, 'suggestxss/run_pwnxss.html')

@login_required
def tool_results(request):
    print("Executing tool_results function")
    results = ToolResult.objects.filter(user=request.user).order_by('-created_at')
    if not results:
        message = "No tool results found."
    else:
        message = None
    print("Finished executing tool_results function")
    return render(request, 'suggestxss/tool_results.html', {'results': results, 'message': message})
    
@login_required
def delete_tool_result(request, result_id):
    print("Executing delete_tool_result function")
    tool_result = get_object_or_404(ToolResult, pk=result_id)
    if tool_result.user == request.user:
        tool_result.delete()
        print("Finished executing delete_tool_result function")
        return redirect('tool_results')  
    else:
        print("Finished executing delete_tool_result function with forbidden access")
        return HttpResponseForbidden("You are not allowed to delete this tool result.")

@csrf_exempt
@login_required
def submit_feedback(request):
    print("Executing submit_feedback function")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            agree = data.get('agree')
            preferred_suggestion = data.get('preferred_suggestion', None)
            user_data = UserData.objects.filter(user=request.user).last()
            
            if user_data:
                if agree:
                    Feedback.objects.create(user_data=user_data, agree=True, preferred_suggestion=user_data.suggest)
                    print(f"User agreed with suggestion: {user_data.suggest}")
                else:
                    Feedback.objects.create(user_data=user_data, agree=False, preferred_suggestion=preferred_suggestion)
                    print(f"User disagreed with suggestion. Preferred suggestion: {preferred_suggestion}")
                
                print("Finished executing submit_feedback function")
                return JsonResponse({'status': 'success'})
            else:
                print("Finished executing submit_feedback function with error: No user data found")
                return JsonResponse({'status': 'failed', 'message': 'No user data found'}, status=400)
            
        except json.JSONDecodeError:
            print("Finished executing submit_feedback function with error: Invalid JSON")
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Finished executing submit_feedback function with error: {str(e)}")
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=500)
    print("Finished executing submit_feedback function with error: Invalid request method")
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=405)

def upload_and_train(request):
    print("Executing upload_and_train function")
    
    # Ensure directories exist
    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)
    
    uploaded_csvs_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_csvs')
    trained_models_dir = os.path.join(settings.MEDIA_ROOT, 'trained_models')

    if not os.path.exists(uploaded_csvs_dir):
        os.makedirs(uploaded_csvs_dir)

    if not os.path.exists(trained_models_dir):
        os.makedirs(trained_models_dir)

    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            file_name = default_storage.save('uploaded_csvs/' + csv_file.name, ContentFile(csv_file.read()))
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # Load CSV file into DataFrame
            data = pd.read_csv(file_path)
            
            # Assuming the last column is the target variable
            X = data.iloc[:, :-1]
            y = data.iloc[:, -1]
            
            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train the model
            model = SVC()
            model.fit(X_train, y_train)
            
            # Calculate accuracy
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save the model to a PKL file
            pkl_file_path = os.path.join(trained_models_dir, 'model.pkl')
            joblib.dump(model, pkl_file_path)
            
            # Provide download link for PKL file
            download_link = os.path.join(settings.MEDIA_URL, 'trained_models', 'model.pkl')
            print(f"Download link: {download_link}")
            print("Finished executing upload_and_train function successfully")
            return render(request, 'suggestxss/upload_and_train.html', {
                'accuracy': accuracy,
                'download_link': download_link
            })
    else:
        form = UploadCSVForm()
    
    print("Finished executing upload_and_train function")
    return render(request, 'suggestxss/upload_and_train.html', {'form': form})

def user_logout(request):
    print("Executing user_logout function")
    logout(request)
    print("Finished executing user_logout function")
    return redirect('home')
