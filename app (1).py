import gradio as gr
import google.generativeai as genai
from PIL import Image
import os

def get_available_model(api_key):
    """Try to find an available text model"""
    genai.configure(api_key=api_key.strip())
    
    # Based on your available models
    models_to_try = [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-pro'
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            return model_name, None
        except Exception as e:
            continue
    
    return None, "No available models found"

def get_available_vision_model(api_key):
    """Try to find an available vision model"""
    genai.configure(api_key=api_key.strip())
    
    # Vision-capable models
    models_to_try = [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-pro-vision'
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            return model_name, None
        except Exception as e:
            continue
    
    return None, "No available vision models found"

def process_multimodal_input(message, image, history, api_key):
    """Process both text and image inputs and generate responses"""
    
    if not api_key or api_key.strip() == "":
        return history + [[message, "⚠️ Please provide your Google Gemini API key in the settings above."]]
    
    try:
        genai.configure(api_key=api_key.strip())
        
        if image is not None:
            # Vision task
            model_name, error = get_available_vision_model(api_key)
            if error:
                return history + [[message, f"❌ {error}"]]
            
            model = genai.GenerativeModel(model_name)
            img = Image.open(image) if isinstance(image, str) else image
            
            if message and message.strip():
                prompt = message
            else:
                prompt = "Describe this image in detail."
            
            response = model.generate_content([prompt, img])
            bot_response = response.text
            
        else:
            # Text only
            if not message or message.strip() == "":
                return history + [[None, "⚠️ Please provide either a text message or an image."]]
            
            model_name, error = get_available_model(api_key)
            if error:
                return history + [[message, f"❌ {error}"]]
            
            model = genai.GenerativeModel(model_name)
            
            # Add conversation context
            full_prompt = message
            if history and len(history) > 0:
                context = ""
                for user_msg, bot_msg in history[-2:]:
                    if user_msg and bot_msg:
                        context += f"User: {user_msg}\nAssistant: {bot_msg}\n"
                if context:
                    full_prompt = f"{context}\nUser: {message}"
            
            response = model.generate_content(full_prompt)
            bot_response = response.text
        
        display_message = message if message and message.strip() else "[Image uploaded]"
        return history + [[display_message, bot_response]]
    
    except Exception as e:
        error_msg = str(e)
        bot_response = f"❌ Error: {error_msg}"
        display_message = message if message and message.strip() else "[Image uploaded]"
        return history + [[display_message, bot_response]]

def generate_image_description(image, api_key):
    """Generate detailed description for uploaded images"""
    
    if not api_key or api_key.strip() == "":
        return "⚠️ Please provide your API key first."
    
    if image is None:
        return "⚠️ Please upload an image."
    
    try:
        model_name, error = get_available_vision_model(api_key)
        if error:
            return f"❌ {error}"
        
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel(model_name)
        img = Image.open(image) if isinstance(image, str) else image
        
        prompt = "Analyze this image in detail: describe subjects, scene, colors, composition, any visible text, mood, and potential context or use cases."
        
        response = model.generate_content([prompt, img])
        return f"✅ Using: {model_name}\n\n{response.text}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

def clear_conversation():
    """Clear the conversation history"""
    return []

def test_api_key(api_key):
    """Test if API key works and show available models"""
    if not api_key or api_key.strip() == "":
        return "⚠️ Please enter an API key first."
    
    try:
        genai.configure(api_key=api_key.strip())
        
        # List all available models
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(f"✅ {model.name}")
        
        if available_models:
            return "✅ API Key is Valid!\n\nAvailable models:\n" + "\n".join(available_models[:15])
        else:
            return "⚠️ API key works but no models found."
    
    except Exception as e:
        return f"❌ API Key Test Failed: {str(e)}"

def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(theme=gr.themes.Soft(), title="Multi-Modal AI Chatbot") as demo:
        gr.Markdown(
            """
            # 🤖 Multi-Modal AI Chatbot
            ### Powered by Google Gemini AI
            
            Chat with AI and analyze images using the latest Gemini models!
            """
        )
        
        with gr.Row():
            with gr.Column():
                api_key_input = gr.Textbox(
                    label="🔑 Google Gemini API Key",
                    placeholder="Paste your API key here",
                    type="password",
                    info="Get from: https://aistudio.google.com/app/apikey"
                )
                with gr.Row():
                    test_btn = gr.Button("🔍 Test API Key", size="sm", variant="secondary")
                test_output = gr.Textbox(label="API Key Status", lines=5, show_copy_button=True)
        
        with gr.Tabs():
            with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=450,
                    bubble_full_width=False,
                    show_copy_button=True
                )
                
                with gr.Row():
                    with gr.Column(scale=4):
                        msg_input = gr.Textbox(
                            label="Your Message",
                            placeholder="Type your message here...",
                            lines=3
                        )
                    with gr.Column(scale=1):
                        image_input = gr.Image(
                            label="Image (Optional)",
                            type="filepath",
                            height=150
                        )
                
                with gr.Row():
                    submit_btn = gr.Button("🚀 Send", variant="primary", scale=2)
                    clear_btn = gr.Button("🗑️ Clear Chat", scale=1)
                
                gr.Examples(
                    examples=[
                        ["Explain artificial intelligence in simple terms"],
                        ["Write a creative short story about space"],
                        ["What are the key differences between Python and JavaScript?"]
                    ],
                    inputs=msg_input,
                    label="💡 Try these examples"
                )
            
            with gr.Tab("🔍 Image Analysis"):
                gr.Markdown("### Upload any image for detailed AI-powered analysis")
                
                with gr.Row():
                    with gr.Column():
                        analysis_image = gr.Image(
                            label="Upload Image",
                            type="filepath",
                            height=300
                        )
                        analyze_btn = gr.Button("🔍 Analyze Image", variant="primary", size="lg")
                    
                    with gr.Column():
                        analysis_output = gr.Textbox(
                            label="Analysis Result",
                            lines=18,
                            show_copy_button=True
                        )
            
            with gr.Tab("📚 Help & Guide"):
                gr.Markdown(
                    """
                    ## 🎯 How to Use This Chatbot
                    
                    ### 1️⃣ Get Your API Key
                    
                    1. Visit: **https://aistudio.google.com/app/apikey**
                    2. Sign in with your Google account
                    3. Click **"Create API Key"**
                    4. Select **"Create API key in new project"**
                    5. Copy the generated key
                    6. Paste it in the field above
                    7. Click **"Test API Key"** to verify
                    
                    ### 2️⃣ Start Chatting
                    
                    **Text Conversations:**
                    - Ask questions about any topic
                    - Request explanations, stories, or creative content
                    - Get coding help or technical explanations
                    
                    **Image Analysis:**
                    - Upload photos to get detailed descriptions
                    - Identify objects, animals, plants, landmarks
                    - Extract text from images
                    - Get recipe suggestions from food photos
                    
                    **Combined (Text + Image):**
                    - Upload image + ask specific questions
                    - "What plant is this and how do I care for it?"
                    - "Explain the code in this screenshot"
                    - "Solve this math problem step by step"
                    
                    ### 3️⃣ Example Prompts
                    
                    📝 **General Knowledge:**
                    - "Explain quantum computing like I'm 10"
                    - "What are the health benefits of green tea?"
                    - "Write a poem about technology"
                    
                    🖼️ **Image Tasks:**
                    - Upload food → "What recipe could I make?"
                    - Upload plant → "Identify this species"
                    - Upload landmark → "Tell me about this place"
                    - Upload document → "Summarize this text"
                    
                    ### 📊 Free Tier Limits
                    
                    - **60 requests per minute**
                    - **1,500 requests per day**
                    - Perfect for learning, demos, and personal use!
                    
                    ### 🌍 Supported Regions
                    
                    ✅ United States, UK, EU, Canada, Australia, Japan, India, Singapore, and more
                    
                    Check availability: https://ai.google.dev/available_regions
                    
                    ### ❓ Common Issues
                    
                    **"No models found"**
                    - Click "Test API Key" to see available models
                    - Wait 2-3 minutes after creating new key
                    - Try generating a fresh API key
                    
                    **"Rate limit exceeded"**
                    - Wait 60 seconds before next request
                    - Free tier has limits (see above)
                    
                    ### 🔒 Privacy & Security
                    
                    - ✅ Your API key is NOT stored on servers
                    - ✅ Conversations are NOT saved permanently
                    - ✅ Images are processed in real-time only
                    - ✅ All data is session-based
                    
                    ### 📞 Need Help?
                    
                    - [Google AI Documentation](https://ai.google.dev/docs)
                    - [Get API Key](https://aistudio.google.com/app/apikey)
                    - [Region Availability](https://ai.google.dev/available_regions)
                    """
                )
        
        # Event handlers
        test_btn.click(
            fn=test_api_key,
            inputs=[api_key_input],
            outputs=[test_output]
        )
        
        submit_btn.click(
            fn=process_multimodal_input,
            inputs=[msg_input, image_input, chatbot, api_key_input],
            outputs=[chatbot]
        ).then(
            lambda: (None, None),
            outputs=[msg_input, image_input]
        )
        
        msg_input.submit(
            fn=process_multimodal_input,
            inputs=[msg_input, image_input, chatbot, api_key_input],
            outputs=[chatbot]
        ).then(
            lambda: (None, None),
            outputs=[msg_input, image_input]
        )
        
        clear_btn.click(fn=clear_conversation, outputs=[chatbot])
        
        analyze_btn.click(
            fn=generate_image_description,
            inputs=[analysis_image, api_key_input],
            outputs=[analysis_output]
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()