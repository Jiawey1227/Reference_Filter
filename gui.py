"""
AI 学术文献相关性评分工具 - 图形界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os

from openai import APIConnectionError, AuthenticationError, APIError

from main import (
    ai_score_ref_column,
    make_openai_client,
    normalize_api_key,
    validate_api_connection,
    highlight_countries,
)


class AIScorerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 文献相关性评分工具")
        self.root.geometry("900x700")

        # 默认配置
        self.api_key_var = tk.StringVar(value="")
        self.base_url_var = tk.StringVar(value="https://aihubmix.com/v1")
        self.model_var = tk.StringVar(value="text-embedding-3-small")
        self.batch_size_var = tk.StringVar(value="20")
        self.delay_var = tk.StringVar(value="1.5")
        self.cache_file_var = tk.StringVar(value="embedding_cache.pkl")
        self.topic_var = tk.StringVar(value="")

        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.running = False

        self.setup_ui()
        self.log("请填写 API Key 后点击“测试连接”。")

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(file_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="浏览...", command=self.select_input_file).grid(row=0, column=2)

        ttk.Label(file_frame, text="输出文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_file_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.select_output_file).grid(row=1, column=2, pady=5)

        # API 配置区域
        api_frame = ttk.LabelFrame(main_frame, text="API 配置", padding="10")
        api_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*").grid(row=0, column=1, padx=5)

        ttk.Label(api_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(api_frame, textvariable=self.base_url_var, width=50).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(api_frame, text="模型:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(api_frame, textvariable=self.model_var, width=50).grid(row=2, column=1, padx=5)

        # 参数配置区域
        param_frame = ttk.LabelFrame(main_frame, text="参数配置", padding="10")
        param_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(param_frame, text="批处理大小:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(param_frame, textvariable=self.batch_size_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(param_frame, text="请求间隔 (秒):").grid(row=0, column=2, sticky=tk.W, padx=20)
        ttk.Entry(param_frame, textvariable=self.delay_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Label(param_frame, text="缓存文件:").grid(row=0, column=4, sticky=tk.W, padx=20)
        ttk.Entry(param_frame, textvariable=self.cache_file_var, width=20).grid(row=0, column=5, padx=5)

        # 主题配置区域
        topic_frame = ttk.LabelFrame(main_frame, text="研究主题", padding="10")
        topic_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.topic_text = scrolledtext.ScrolledText(topic_frame, height=6, width=80)
        self.topic_text.grid(row=0, column=0)
        self.topic_text.insert(tk.END, self.topic_var.get())

        # 控制按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="开始评分", command=self.start_scoring)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_scoring, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.test_conn_btn = ttk.Button(btn_frame, text="测试连接", command=self.test_api_connection)
        self.test_conn_btn.grid(row=0, column=2, padx=5)

        # 高亮按钮
        self.highlight_btn = ttk.Button(btn_frame, text="国家高亮", command=self.run_highlight)
        self.highlight_btn.grid(row=0, column=3, padx=5)

        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="进度", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.grid(row=1, column=0, sticky=tk.W)

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def log(self, message):
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, lambda msg=message: self.log(msg))
            return
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _format_error(self, error):
        parts = [str(error)]
        cause = getattr(error, "__cause__", None)
        context = getattr(error, "__context__", None)
        if cause:
            parts.append(f"底层原因：{repr(cause)}")
        elif context:
            parts.append(f"底层原因：{repr(context)}")
        return "；".join(part for part in parts if part)

    def select_input_file(self):
        filename = filedialog.askopenfilename(
            title="选择输入 Excel 文件",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filename:
            self.input_file_var.set(filename)
            # 自动设置输出文件名
            base, ext = os.path.splitext(filename)
            self.output_file_var.set(f"{base}_result.xlsx")

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="选择输出文件位置",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if filename:
            self.output_file_var.set(filename)

    def start_scoring(self):
        input_file = self.input_file_var.get()
        output_file = self.output_file_var.get()

        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("错误", "请选择有效的输入文件")
            return

        if not output_file:
            messagebox.showerror("错误", "请选择输出文件位置")
            return

        # 运行前验证 API 连接
        self.log("正在验证 API 连接...")
        if not self._validate_api():
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)

        # 在新线程中运行评分
        thread = threading.Thread(target=self.run_scoring, daemon=True)
        thread.start()

    def stop_scoring(self):
        self.running = False
        self.log("正在停止...")

    def _check_cancel(self):
        """取消检查函数"""
        return not self.running

    def run_scoring(self):
        try:
            # 获取主题
            topic = self.topic_text.get("1.0", tk.END).strip()

            # 解析参数
            batch_size = int(self.batch_size_var.get())
            delay = float(self.delay_var.get())

            self.log(f"开始处理: {self.input_file_var.get()}")
            self.log(f"主题：{topic[:50]}...")

            ai_score_ref_column(
                input_file=self.input_file_var.get(),
                output_file=self.output_file_var.get(),
                api_key=self.api_key_var.get(),
                base_url=self.base_url_var.get(),
                model=self.model_var.get(),
                topic=topic,
                batch_size=batch_size,
                delay=delay,
                cache_file=self.cache_file_var.get(),
                progress_callback=self._on_progress,
                cancel_check=self._check_cancel,
            )

            if not self.running:
                self.root.after(0, lambda: self.log("用户取消操作"))
                return

            # 评分完成后自动执行国家区域高亮
            output_file = self.output_file_var.get()
            self.log("正在执行国家区域高亮标记...")
            try:
                highlight_countries(output_file)
                self.log("国家区域高亮标记完成")
            except Exception as e:
                self.log(f"国家区域高亮标记失败：{e}")

            self.root.after(0, lambda: messagebox.showinfo("完成", f"评分完成！\n结果已保存到：{output_file}"))

        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"处理失败：{msg}"))
            self.log(f"错误：{error_msg}")
        finally:
            self.running = False
            self.root.after(0, self._on_complete)

    def _on_progress(self, progress, status, done=False):
        """进度回调（在非主线程中调用）"""
        if done:
            return
        self.root.after(0, lambda: self._update_progress_ui(progress, status))

    def _update_progress_ui(self, progress, status):
        """在主线程中更新 UI"""
        self.progress_var.set(progress)
        self.status_label.config(text=status)
        self.log(status)

    def _on_complete(self):
        """评分完成后恢复按钮状态"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def run_highlight(self):
        """单独运行国家区域高亮"""
        filename = filedialog.askopenfilename(
            title="选择要处理的 Excel 文件",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not filename:
            return
        try:
            highlight_countries(filename)
            messagebox.showinfo("完成", f"国家区域高亮完成！\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"高亮处理失败：{str(e)}")

    def test_api_connection(self):
        """测试 API 连接"""
        self.log("正在测试 API 连接...")

        api_key = self.api_key_var.get()
        base_url = self.base_url_var.get()
        model = self.model_var.get()

        def test_thread():
            try:
                client = make_openai_client(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=30
                )
                client.embeddings.create(
                    model=model,
                    input=["connection_test"]
                )
                self.root.after(0, lambda: messagebox.showinfo(
                    "连接成功",
                    f"API 连接正常\n服务：{base_url}\n模型：{model}"
                ))
                self.root.after(0, lambda: self.log("API 连接测试成功"))
            except AuthenticationError:
                self.root.after(0, lambda: self.log("API 连接测试失败：认证错误"))
                self.root.after(0, lambda: messagebox.showerror(
                    "认证失败",
                    "API Key 无效或已过期，请更换有效的密钥"
                ))
            except APIConnectionError as e:
                error_msg = self._format_error(e)
                self.root.after(0, lambda msg=error_msg: self.log(f"API 连接测试失败：{msg}"))
                self.root.after(0, lambda: messagebox.showerror(
                    "连接失败",
                    f"无法连接到 API 服务\n{base_url}\n\n可能原因：\n1. 网络问题或防火墙限制\n2. API 服务已下线\n3. DNS 解析失败"
                ))
            except APIError as e:
                error_msg = e.message if hasattr(e, 'message') else str(e)
                self.root.after(0, lambda msg=error_msg: self.log(f"API 连接测试失败：{msg}"))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                    "API 错误",
                    f"API 返回错误：{msg}"
                ))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: self.log(f"API 连接测试失败：{msg}"))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                    "未知错误",
                    f"发生未知错误：{msg}"
                ))

        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def _validate_api(self):
        """运行前快速验证 API 连接"""
        api_key = self.api_key_var.get()
        base_url = self.base_url_var.get()
        model = self.model_var.get()

        try:
            client = make_openai_client(
                api_key=api_key,
                base_url=base_url,
                timeout=30
            )
            client.embeddings.create(
                model=model,
                input=["validate"]
            )
            self.log("API 连接验证通过")
            return True
        except AuthenticationError:
            self.log("API 验证失败：认证错误")
            messagebox.showerror(
                "认证失败",
                "API Key 无效或已过期，请更换有效的密钥"
            )
            return False
        except APIConnectionError as e:
            self.log(f"API 验证失败：{self._format_error(e)}")
            messagebox.showerror(
                "连接失败",
                f"无法连接到 API 服务\n{base_url}\n\n请检查：\n1. 网络连接\n2. API 服务状态\n3. 防火墙/代理设置"
            )
            return False
        except Exception as e:
            messagebox.showerror("验证失败", f"API 验证失败：{str(e)}")
            self.log(f"API 验证失败：{str(e)}")
            return False


def main():
    root = tk.Tk()
    app = AIScorerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
