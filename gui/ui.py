import customtkinter as ctk

# 设置应用主题
ctk.set_appearance_mode("System")  # 或 "Dark" / "Light"
ctk.set_default_color_theme("blue")  # 可选主题

# 创建主窗口
app = ctk.CTk()
app.title("ClipTale App")
app.geometry("400x300")


# 定义按钮回调函数
def button_callback():
    result = "Functional code executed!"
    label.configure(text=f"Result: {result}")


# 添加按钮和标签
button = ctk.CTkButton(app, text="Run Functional Code", command=button_callback)
button.pack(pady=20)

label = ctk.CTkLabel(app, text="Click the button to start")
label.pack(pady=10)

# 运行应用
app.mainloop()
