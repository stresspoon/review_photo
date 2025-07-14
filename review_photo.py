import os
import sys
import time
import threading
import re
import requests
import urllib.parse
import subprocess
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk

# exe로 빌드된 경우 처리
def resource_path(relative_path):
    """PyInstaller 빌드 시 리소스 경로 처리"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_chrome_driver():
    """ChromeDriver 가져오기 - exe 빌드 고려"""
    bundled_driver = resource_path("chromedriver.exe")
    if os.path.exists(bundled_driver):
        return Service(bundled_driver)
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        return Service(ChromeDriverManager().install())
    except Exception as e:
        messagebox.showerror("오류", f"ChromeDriver를 찾을 수 없습니다: {e}")
        return None

def get_unique_filename(save_path):
    """파일명 중복을 방지하기 위한 함수"""
    if not os.path.exists(save_path):
        return save_path
    
    base, ext = os.path.splitext(save_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"

def extract_product_info(url):
    """URL에서 상품 정보 추출"""
    # 예: https://brand.naver.com/makeman/products/3472994718#REVIEW
    match = re.search(r'/products/(\d+)', url)
    if match:
        return match.group(1)
    
    # 다른 형식의 URL도 처리
    # 예: https://smartstore.naver.com/makeman/products/3472994718
    match = re.search(r'products/(\d+)', url)
    if match:
        return match.group(1)
    
    return None

def download_review_images(product_url, download_dir, log_widget, max_pages=10, progress_callback=None):
    """스마트스토어 리뷰 이미지 다운로드"""
    
    # 다운로드 폴더 생성
    product_id = extract_product_info(product_url)
    if not product_id:
        log_widget.insert(tk.END, "❌ URL에서 상품 ID를 찾을 수 없습니다.\n")
        return
    
    review_folder = os.path.join(download_dir, f"reviews_{product_id}")
    os.makedirs(review_folder, exist_ok=True)
    
    log_widget.insert(tk.END, f"📁 상품 ID: {product_id}\n")
    log_widget.insert(tk.END, f"📂 저장 폴더: {review_folder}\n")
    log_widget.insert(tk.END, "-" * 70 + "\n")
    
    # Selenium 드라이버 설정
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    service = get_chrome_driver()
    if not service:
        log_widget.insert(tk.END, "❌ ChromeDriver를 초기화할 수 없습니다.\n")
        return
    
    driver = None
    all_image_urls = set()
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(product_url)
        wait = WebDriverWait(driver, 10)
        
        # 페이지 로드 대기
        time.sleep(3)
        
        # 리뷰 탭 클릭 (이미 #REVIEW가 URL에 있어도 클릭)
        try:
            review_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '#REVIEW')]")))
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)
            log_widget.insert(tk.END, "✅ 리뷰 탭으로 이동\n")
        except:
            log_widget.insert(tk.END, "ℹ️ 이미 리뷰 탭에 있습니다.\n")
        
        # 각 페이지 순회
        for page_num in range(1, max_pages + 1):
            log_widget.insert(tk.END, f"\n📄 {page_num} 페이지 처리 중...\n")
            log_widget.see(tk.END)
            
            if page_num > 1:
                # 페이지 번호 클릭
                try:
                    # 페이지네이션 찾기
                    pagination = driver.find_element(By.CSS_SELECTOR, "div._2LCk94m75R")
                    page_links = pagination.find_elements(By.TAG_NAME, "a")
                    
                    clicked = False
                    for link in page_links:
                        if link.text.strip() == str(page_num):
                            driver.execute_script("arguments[0].click();", link)
                            clicked = True
                            time.sleep(2)
                            break
                    
                    if not clicked:
                        # 다음 버튼으로 이동 시도
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.UWN4IvaQza")
                        if next_btn and "disabled" not in next_btn.get_attribute("class"):
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(2)
                        else:
                            log_widget.insert(tk.END, f"⚠️ {page_num} 페이지로 이동할 수 없습니다.\n")
                            break
                except Exception as e:
                    log_widget.insert(tk.END, f"⚠️ 페이지 이동 실패: {e}\n")
                    break
            
            # 현재 페이지의 리뷰 이미지 수집
            page_images = collect_review_images(driver, log_widget)
            all_image_urls.update(page_images)
            
            log_widget.insert(tk.END, f"  → 이 페이지에서 {len(page_images)}개 이미지 발견\n")
            
            if progress_callback:
                progress_callback(page_num, max_pages)
        
        # 이미지 다운로드
        log_widget.insert(tk.END, f"\n💾 총 {len(all_image_urls)}개 이미지 다운로드 시작...\n")
        log_widget.insert(tk.END, "-" * 70 + "\n")
        
        download_count = 0
        total = len(all_image_urls)
        
        for idx, img_url in enumerate(sorted(all_image_urls), 1):
            filename = f"review_{product_id}_{idx:04d}.jpg"
            save_path = os.path.join(review_folder, filename)
            save_path = get_unique_filename(save_path)
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': product_url
                }
                
                # 썸네일 URL을 원본 이미지 URL로 변환
                original_url = convert_to_original_url(img_url)
                
                response = requests.get(original_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    download_count += 1
                    log_widget.insert(tk.END, f"[{idx}/{total}] ✅ {os.path.basename(save_path)}\n")
                else:
                    log_widget.insert(tk.END, f"[{idx}/{total}] ❌ HTTP {response.status_code}\n")
            except Exception as e:
                log_widget.insert(tk.END, f"[{idx}/{total}] ❌ 오류: {str(e)[:50]}...\n")
            
            log_widget.see(tk.END)
        
        log_widget.insert(tk.END, f"\n✅ 다운로드 완료: {download_count}/{total}개 성공\n")
        
    except Exception as e:
        log_widget.insert(tk.END, f"\n❌ 오류 발생: {e}\n")
        import traceback
        log_widget.insert(tk.END, f"{traceback.format_exc()}\n")
    finally:
        if driver:
            driver.quit()
        log_widget.insert(tk.END, "\n🎉 작업 완료!\n")
        log_widget.see(tk.END)

def collect_review_images(driver, log_widget):
    """현재 페이지의 리뷰 이미지 수집"""
    image_urls = set()
    
    try:
        # 리뷰 컨테이너 찾기
        review_containers = driver.find_elements(By.CSS_SELECTOR, "div.YkRE5A9l4P")
        log_widget.insert(tk.END, f"  → {len(review_containers)}개 리뷰 발견\n")
        
        for review in review_containers:
            # 리뷰 내 이미지 찾기
            images = review.find_elements(By.CSS_SELECTOR, "img._3wVTRzzPzH, img._2SqzkWDFme")
            
            for img in images:
                src = img.get_attribute('src')
                if src and 'phinf.pstatic.net' in src:
                    image_urls.add(src)
        
        # 추가로 다른 형식의 이미지도 찾기
        all_images = driver.find_elements(By.CSS_SELECTOR, "div._25CKxIKjAk img")
        for img in all_images:
            src = img.get_attribute('src')
            if src and 'phinf.pstatic.net' in src:
                image_urls.add(src)
                
    except Exception as e:
        log_widget.insert(tk.END, f"  ⚠️ 이미지 수집 중 오류: {e}\n")
    
    return image_urls

def convert_to_original_url(thumb_url):
    """썸네일 URL을 원본 이미지 URL로 변환"""
    # 네이버 이미지 URL 패턴
    # 썸네일: https://phinf.pstatic.net/.../20240101_123_456789_1.jpg?type=w200
    # 원본: https://phinf.pstatic.net/.../20240101_123_456789_1.jpg
    
    # ?type= 파라미터 제거
    if '?type=' in thumb_url:
        return thumb_url.split('?type=')[0]
    
    # 다른 파라미터도 제거
    if '?' in thumb_url:
        return thumb_url.split('?')[0]
    
    return thumb_url

def create_gui():
    """GUI 인터페이스 생성"""
    root = tk.Tk()
    root.title("네이버 스마트스토어 리뷰 이미지 다운로더")
    root.geometry("900x700")
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 제목
    title_label = tk.Label(root, text="스마트스토어 리뷰 이미지 다운로더", 
                          font=("Arial", 16, "bold"), bg="#03C75A", fg="white", pady=10)
    title_label.pack(fill=tk.X)
    
    # URL 입력 프레임
    url_frame = tk.Frame(root, bg="#f5f5f5")
    url_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(url_frame, text="상품 URL:", font=("Arial", 10), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
    url_entry = tk.Entry(url_frame, width=60, font=("Arial", 10))
    url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    url_entry.insert(0, "https://brand.naver.com/makeman/products/3472994718#REVIEW")
    
    # 설정 프레임
    settings_frame = tk.Frame(root, bg="#f5f5f5")
    settings_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # 페이지 수 설정
    tk.Label(settings_frame, text="다운로드할 페이지 수:", font=("Arial", 10), bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
    page_spinbox = tk.Spinbox(settings_frame, from_=1, to=100, width=10, font=("Arial", 10))
    page_spinbox.delete(0, tk.END)
    page_spinbox.insert(0, "10")
    page_spinbox.pack(side=tk.LEFT, padx=5)
    tk.Label(settings_frame, text="페이지", font=("Arial", 10), bg="#f5f5f5").pack(side=tk.LEFT)
    
    # 다운로드 폴더 선택 프레임
    folder_frame = tk.Frame(root)
    folder_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(folder_frame, text="다운로드 폴더:", font=("Arial", 10)).pack(side=tk.LEFT)
    folder_entry = tk.Entry(folder_frame, width=50, font=("Arial", 10))
    folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    folder_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads", "smartstore_reviews"))
    
    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder)
    
    tk.Button(folder_frame, text="폴더 선택", command=browse_folder).pack(side=tk.RIGHT)
    
    # 진행률 표시
    progress_frame = tk.Frame(root)
    progress_frame.pack(fill=tk.X, padx=10, pady=5)
    
    progress_label = tk.Label(progress_frame, text="대기 중...", font=("Arial", 10))
    progress_label.pack(side=tk.LEFT)
    
    progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
    progress_bar.pack(side=tk.LEFT, padx=20)
    
    # 로그 출력 영역
    log_frame = tk.Frame(root)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    tk.Label(log_frame, text="다운로드 로그:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
    log_widget = scrolledtext.ScrolledText(log_frame, height=20, font=("Consolas", 9))
    log_widget.pack(fill=tk.BOTH, expand=True)
    
    # 버튼 프레임
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def update_progress(current, total):
        progress = (current / total) * 100
        progress_bar['value'] = progress
        progress_label.config(text=f"페이지 진행률: {current}/{total} ({progress:.1f}%)")
        root.update_idletasks()
    
    def start_download():
        url = url_entry.get().strip()
        folder = folder_entry.get().strip()
        max_pages = int(page_spinbox.get())
        
        if not url:
            messagebox.showerror("오류", "URL을 입력해주세요.")
            return
        
        if not folder:
            messagebox.showerror("오류", "다운로드 폴더를 선택해주세요.")
            return
        
        # 로그 초기화
        log_widget.delete(1.0, tk.END)
        log_widget.insert(tk.END, f"🚀 리뷰 이미지 다운로드 시작...\n")
        log_widget.insert(tk.END, f"📁 URL: {url}\n")
        log_widget.insert(tk.END, f"📄 페이지 수: {max_pages}페이지\n")
        log_widget.insert(tk.END, f"📂 저장 폴더: {folder}\n")
        log_widget.insert(tk.END, "=" * 70 + "\n\n")
        
        # 버튼 상태 변경
        download_btn.config(state=tk.DISABLED, text="다운로드 중...")
        progress_label.config(text="준비 중...")
        progress_bar['value'] = 0
        
        # 별도 스레드에서 다운로드 실행
        def download_thread():
            try:
                download_review_images(url, folder, log_widget, max_pages, update_progress)
            except Exception as e:
                log_widget.insert(tk.END, f"\n❌ 예상치 못한 오류: {e}\n")
                import traceback
                log_widget.insert(tk.END, f"{traceback.format_exc()}\n")
            finally:
                download_btn.config(state=tk.NORMAL, text="다운로드 시작")
                progress_label.config(text="완료!")
                progress_bar['value'] = 100
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    download_btn = tk.Button(button_frame, text="다운로드 시작", command=start_download, 
                           bg="#03C75A", fg="white", font=("Arial", 12, "bold"),
                           padx=20, pady=10)
    download_btn.pack(side=tk.LEFT, padx=5)
    
    def clear_log():
        log_widget.delete(1.0, tk.END)
        progress_label.config(text="대기 중...")
        progress_bar['value'] = 0
    
    tk.Button(button_frame, text="로그 지우기", command=clear_log,
              font=("Arial", 10), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    def open_folder():
        folder = folder_entry.get().strip()
        if folder and os.path.exists(folder):
            try:
                if platform.system() == "Windows":
                    os.startfile(folder)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", folder])
                else:
                    subprocess.call(["xdg-open", folder])
            except Exception as e:
                messagebox.showerror("오류", f"폴더를 열 수 없습니다: {e}")
        else:
            messagebox.showwarning("경고", "폴더가 존재하지 않습니다.")
    
    tk.Button(button_frame, text="폴더 열기", command=open_folder,
              font=("Arial", 10), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
    
    # 도움말
    help_text = """
    사용 방법:
    1. 네이버 스마트스토어 상품 URL 입력
    2. 다운로드할 리뷰 페이지 수 설정 (기본 10페이지)
    3. 저장할 폴더 선택
    4. '다운로드 시작' 클릭
    
    ※ 지원 URL 형식:
    - https://brand.naver.com/브랜드명/products/상품ID
    - https://smartstore.naver.com/스토어명/products/상품ID
    """
    
    def show_help():
        messagebox.showinfo("도움말", help_text)
    
    tk.Button(button_frame, text="도움말", command=show_help,
              font=("Arial", 10), padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
    
    # 종료 버튼
    tk.Button(button_frame, text="종료", command=root.quit,
              font=("Arial", 10), padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
    
    return root

if __name__ == "__main__":
    try:
        root = create_gui()
        root.mainloop()
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        if platform.system() == "Windows":
            input("엔터를 눌러 종료하세요...")