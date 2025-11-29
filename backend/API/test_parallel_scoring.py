
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============= GIẢ LẬP CÁC HÀM SCORING =============

def score_experience(cv, jd):
    """Giả lập: mất 1.5s"""
    time.sleep(1.5)
    return {'experience_score': 27.5, 'max': 30}


def score_technical(cv, jd):
    """Giả lập: mất 2s"""
    time.sleep(2.0)
    return {'technical_score': 35.2, 'max': 40}


def score_soft_skills(cv, jd):
    """Giả lập: mất 2s"""
    time.sleep(2.0)
    return {'soft_skills_score': 24.5, 'max': 30}


def score_tools(cv, jd):
    """Giả lập: mất 1s"""
    time.sleep(1.0)
    return {'tools_score': 18.0, 'max': 20}


def score_relevance(cv, jd):
    """Giả lập: mất 1s"""
    time.sleep(1.0)
    return {'relevance_score': 8.5, 'max': 10}


# ============= CÁCH 1: SEQUENTIAL (Chậm) =============

def score_cv_sequential(cv_data, jd_data):
    """Chạy tuần tự - chậm"""
    start = time.time()
    
    result1 = score_experience(cv_data, jd_data)
    result2 = score_technical(cv_data, jd_data)
    result3 = score_soft_skills(cv_data, jd_data)
    result4 = score_tools(cv_data, jd_data)
    result5 = score_relevance(cv_data, jd_data)
    
    end = time.time()
    
    return {
        **result1,
        **result2,
        **result3,
        **result4,
        **result5,
        'total_time': round(end - start, 2)
    }


# ============= CÁCH 2: PARALLEL (Nhanh) =============

def score_cv_parallel(cv_data, jd_data):
    """Chạy song song - nhanh"""
    start = time.time()
    
    # Tạo ThreadPool với 5 threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit tất cả tasks cùng lúc
        future_exp = executor.submit(score_experience, cv_data, jd_data)
        future_tech = executor.submit(score_technical, cv_data, jd_data)
        future_soft = executor.submit(score_soft_skills, cv_data, jd_data)
        future_tools = executor.submit(score_tools, cv_data, jd_data)
        future_rel = executor.submit(score_relevance, cv_data, jd_data)
        
        # Đợi tất cả tasks hoàn thành và lấy kết quả
        result1 = future_exp.result()    # Đợi experience xong
        result2 = future_tech.result()   # Đợi technical xong
        result3 = future_soft.result()   # Đợi soft skills xong
        result4 = future_tools.result()  # Đợi tools xong
        result5 = future_rel.result()    # Đợi relevance xong
    
    end = time.time()
    
    return {
        **result1,
        **result2,
        **result3,
        **result4,
        **result5,
        'total_time': round(end - start, 2)
    }


# ============= CÁCH 3: PARALLEL + DYNAMIC (Tốt nhất) =============

def score_cv_parallel_dynamic(cv_data, jd_data):
    """Chạy song song + xử lý kết quả ngay khi có"""
    start = time.time()
    
    # Định nghĩa các tasks
    tasks = {
        'experience': score_experience,
        'technical': score_technical,
        'soft_skills': score_soft_skills,
        'tools': score_tools,
        'relevance': score_relevance
    }
    
    results = {}
    
    # Submit tất cả tasks
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit và map future với tên task
        future_to_name = {
            executor.submit(func, cv_data, jd_data): name 
            for name, func in tasks.items()
        }
        
        # Xử lý kết quả ngay khi có (không cần đợi tất cả)
        for future in as_completed(future_to_name):
            task_name = future_to_name[future]
            try:
                result = future.result()
                results.update(result)
                print(f"✓ {task_name} completed")
            except Exception as e:
                print(f"✗ {task_name} failed: {e}")
    
    end = time.time()
    results['total_time'] = round(end - start, 2)
    
    return results


# ============= TEST =============

if __name__ == "__main__":
    print(time.sleep(1.5))
    cv_data = {'name': 'John Doe'}
    jd_data = {'title': 'Senior Developer'}
    
    print("=" * 70)
    print("COMPARING: SEQUENTIAL vs PARALLEL")
    print("=" * 70)
    print()
    
    # Test 1: Sequential
    print("1. SEQUENTIAL (Tuần tự):")
    print("   Experience (1.5s) → Technical (2s) → Soft (2s) → Tools (1s) → Relevance (1s)")
    result1 = score_cv_sequential(cv_data, jd_data)
    print(f"   ⏱️  Total time: {result1['total_time']}s")
    print()
    
    # Test 2: Parallel
    print("2. PARALLEL (Song song):")
    print("   All tasks run simultaneously...")
    result2 = score_cv_parallel(cv_data, jd_data)
    print(f"   ⏱️  Total time: {result2['total_time']}s")
    print()
    
    # Test 3: Parallel Dynamic
    print("3. PARALLEL DYNAMIC (Song song + real-time):")
    result3 = score_cv_parallel_dynamic(cv_data, jd_data)
    print(f"   ⏱️  Total time: {result3['total_time']}s")
    print()
    
    # So sánh
    print("=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Sequential:        {result1['total_time']}s  (baseline)")
    print(f"Parallel:          {result2['total_time']}s  ({result1['total_time']/result2['total_time']:.1f}x faster)")
    print(f"Parallel Dynamic:  {result3['total_time']}s  ({result1['total_time']/result3['total_time']:.1f}x faster)")
    print()
    print(f"Speedup: {result1['total_time'] - result2['total_time']:.1f}s saved!")

