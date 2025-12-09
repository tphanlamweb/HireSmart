// Internationalization (i18n) System
const translations = {
    vi: {
        // Navigation
        'nav.home': 'Trang chủ',
        'nav.about': 'Giới thiệu',
        'nav.activities': 'Hoạt động',
        'nav.jobs': 'Jobs',
        'nav.contact': 'Liên hệ',
        'nav.hr_login': 'Đăng nhập HR',
        
        // Hero Section
        'hero.title1': 'Kết nối tài năng',
        'hero.subtitle1': 'Phát triển tương lai cùng HireSmart',
        'hero.title2': 'Đội ngũ chuyên nghiệp',
        'hero.subtitle2': 'Môi trường làm việc năng động và sáng tạo',
        'hero.title3': 'Cơ hội phát triển',
        'hero.subtitle3': 'Nơi bạn có thể tỏa sáng và thăng tiến',
        'hero.cta': 'Khám phá ngay',
        'hero.cta2': 'Xem hoạt động',
        'hero.cta3': 'Liên hệ ngay',
        
        // About Section
        'about.title': 'Giới thiệu về HireSmart',
        'about.who': 'Chúng tôi là ai?',
        'about.desc1': 'HireSmart là công ty hoạt động trong lĩnh vực chăm sóc sức khỏe, với đội ngũ trẻ trung và môi trường chuyên nghiệp. Chúng tôi luôn tìm kiếm những cá nhân có đam mê và sáng tạo để cùng phát triển.',
        'about.desc2': 'Với hơn 10 năm kinh nghiệm trong ngành, chúng tôi tự hào là đối tác tin cậy của hàng nghìn khách hàng và đã xây dựng được một đội ngũ nhân viên tận tâm, chuyên nghiệp.',
        'about.vision': 'Tầm nhìn:',
        'about.vision_text': 'Trở thành công ty hàng đầu trong lĩnh vực chăm sóc sức khỏe tại Việt Nam.',
        'about.mission': 'Sứ mệnh:',
        'about.mission_text': 'Mang đến giải pháp chăm sóc sức khỏe toàn diện và chất lượng cao cho cộng đồng.',
        
        // Highlights Section
        'highlights.title': 'Hoạt động nổi bật',
        'highlight1.title': 'Workshop Kỹ năng 2024',
        'highlight1.desc': 'Chương trình đào tạo kỹ năng chuyên môn và mềm cho toàn thể nhân viên, giúp nâng cao năng lực và hiệu quả công việc.',
        'highlight2.title': 'Sự kiện Team Building',
        'highlight2.desc': 'Hoạt động gắn kết đội nhóm tại Đà Lạt, tạo môi trường vui vẻ, thân thiện và tăng cường tinh thần đồng đội giữa các phòng ban.',
        'highlight3.title': 'Chương trình CSR',
        'highlight3.desc': 'Đồng hành cùng cộng đồng qua các hoạt động từ thiện, khám sức khỏe miễn phí cho người nghèo và trẻ em vùng cao.',
        'highlight4.title': 'Giải thưởng "Nơi làm việc tốt nhất"',
        'highlight4.desc': 'HireSmart vinh dự nhận giải thưởng "Best Place to Work 2024" - công nhận cho môi trường làm việc chuyên nghiệp và nhân văn.',
        'highlight5.title': 'Hội thảo chuyên ngành',
        'highlight5.desc': 'Tổ chức hội thảo với các chuyên gia hàng đầu về xu hướng mới trong ngành chăm sóc sức khỏe và công nghệ y tế.',
        'highlight6.title': 'Chương trình Onboarding',
        'highlight6.desc': 'Chào đón thành viên mới với chương trình định hướng toàn diện, giúp hòa nhập nhanh chóng vào văn hóa công ty.',
        
        // Contact Section
        'contact.title': 'Liên hệ với chúng tôi',
        'contact.name': 'Họ và tên *',
        'contact.email': 'Email *',
        'contact.message': 'Nội dung liên hệ *',
        'contact.submit': 'Gửi tin nhắn',
        'contact.address': 'Địa chỉ',
        'contact.phone': 'Số điện thoại',
        'contact.work_hours': 'Giờ làm việc',
        
        // Footer
        'footer.company': 'HireSmart Company',
        'footer.tagline': 'Kết nối tài năng - Phát triển tương lai',
        'footer.links': 'Liên kết',
        'footer.info': 'Thông tin',
        'footer.contact': 'Liên hệ',
        'footer.copyright': '© 2025 HireSmart Company - Hệ thống Quét CV. All rights reserved.',
        'footer.developed': 'Phát triển bởi Nhóm Sinh Viên Dự Án Quét CV - Đại học Duy Tân'
    },
    en: {
        // Navigation
        'nav.home': 'Home',
        'nav.about': 'About',
        'nav.activities': 'Activities',
        'nav.jobs': 'Jobs',
        'nav.contact': 'Contact',
        'nav.hr_login': 'HR Login',
        
        // Hero Section
        'hero.title1': 'Connect Talent',
        'hero.subtitle1': 'Develop the future with HireSmart',
        'hero.title2': 'Professional Team',
        'hero.subtitle2': 'Dynamic and creative working environment',
        'hero.title3': 'Growth Opportunities',
        'hero.subtitle3': 'Where you can shine and advance',
        'hero.cta': 'Explore Now',
        'hero.cta2': 'View Activities',
        'hero.cta3': 'Contact Now',
        
        // About Section
        'about.title': 'About HireSmart',
        'about.who': 'Who are we?',
        'about.desc1': 'HireSmart is a company operating in the healthcare sector, with a young team and professional environment. We are always looking for passionate and creative individuals to develop together.',
        'about.desc2': 'With more than 10 years of experience in the industry, we are proud to be a trusted partner of thousands of customers and have built a dedicated, professional team.',
        'about.vision': 'Vision:',
        'about.vision_text': 'Become the leading company in the healthcare sector in Vietnam.',
        'about.mission': 'Mission:',
        'about.mission_text': 'Provide comprehensive and high-quality healthcare solutions for the community.',
        
        // Highlights Section
        'highlights.title': 'Featured Activities',
        'highlight1.title': 'Skills Workshop 2024',
        'highlight1.desc': 'Professional and soft skills training program for all employees, helping to improve capacity and work efficiency.',
        'highlight2.title': 'Team Building Event',
        'highlight2.desc': 'Team bonding activities in Da Lat, creating a fun, friendly environment and strengthening team spirit between departments.',
        'highlight3.title': 'CSR Program',
        'highlight3.desc': 'Accompanying the community through charity activities, free health check-ups for the poor and children in highland areas.',
        'highlight4.title': '"Best Place to Work" Award',
        'highlight4.desc': 'HireSmart is honored to receive the "Best Place to Work 2024" award - recognition for professional and humane working environment.',
        'highlight5.title': 'Professional Seminar',
        'highlight5.desc': 'Organizing seminars with leading experts on new trends in healthcare and medical technology.',
        'highlight6.title': 'Onboarding Program',
        'highlight6.desc': 'Welcoming new members with comprehensive orientation program, helping them quickly integrate into company culture.',
        
        // Contact Section
        'contact.title': 'Contact Us',
        'contact.name': 'Full Name *',
        'contact.email': 'Email *',
        'contact.message': 'Contact Content *',
        'contact.submit': 'Send Message',
        'contact.address': 'Address',
        'contact.phone': 'Phone',
        'contact.work_hours': 'Working Hours',
        
        // Footer
        'footer.company': 'HireSmart Company',
        'footer.tagline': 'Connect Talent - Develop Future',
        'footer.links': 'Links',
        'footer.info': 'Information',
        'footer.contact': 'Contact',
        'footer.copyright': '© 2025 HireSmart Company - CV Scanning System. All rights reserved.',
        'footer.developed': 'Developed by CV Scanning Project Student Group - Duy Tan University'
    }
};

// Language management
let currentLanguage = localStorage.getItem('language') || 'vi';

function setLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    updateLanguageUI();
    translatePage();
}

function updateLanguageUI() {
    const currentLangSpan = document.getElementById('currentLang');
    if (currentLangSpan) {
        currentLangSpan.textContent = currentLanguage === 'vi' ? '🇻🇳' : '🇺🇸';
    }
}

function translatePage() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[currentLanguage] && translations[currentLanguage][key]) {
            element.textContent = translations[currentLanguage][key];
        }
    });
}

// Initialize language system
function initializeLanguage() {
    updateLanguageUI();
    translatePage();
    
    // Add click handlers for language options
    document.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
        });
    });
}

window.addEventListener('scroll', function() {
    const header = document.getElementById('header');
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Slider functionality
let slideIndex = 0;
let slideTimer;

function showSlide(n) {
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');
    
    if (n >= slides.length) { slideIndex = 0; }
    if (n < 0) { slideIndex = slides.length - 1; }
    
    slides.forEach(slide => slide.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));
    
    slides[slideIndex].classList.add('active');
    dots[slideIndex].classList.add('active');
}

function nextSlide() {
    slideIndex++;
    showSlide(slideIndex);
}

function currentSlide(n) {
    slideIndex = n;
    showSlide(slideIndex);
    resetTimer();
}

function resetTimer() {
    clearInterval(slideTimer);
    slideTimer = setInterval(nextSlide, 5000);
}

// Auto slide every 5 seconds
slideTimer = setInterval(nextSlide, 5000);

// Initialize first slide
showSlide(slideIndex);

// Contact form submission
document.getElementById('contactForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        message: document.getElementById('message').value
    };

    // Gửi dữ liệu đến backend
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        // Show success modal
        document.getElementById('successModal').style.display = 'flex';
        
        // Reset form
        document.getElementById('contactForm').reset();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra. Vui lòng thử lại!');
    });
});

// Close modal
function closeModal() {
    document.getElementById('successModal').style.display = 'none';
}

// Close modal when clicking outside
window.addEventListener('click', function(e) {
    const modal = document.getElementById('successModal');
    if (e.target === modal) {
        closeModal();
    }
});

// HR Login handler
function handleHRLogin(event) {
    event.preventDefault();
    // Chuyển đến trang dashboard HR
    window.location.href = "../html/Login.html";
    // Hoặc hiển thị form đăng nhập
    // showLoginForm();
}
// User authentication and UI management
function initializeUserAuth() {
    const user = localStorage.getItem('loggedInUser');
    const logoutBtn = document.getElementById('logoutBtn');
    const dashboardBtn = document.getElementById('dashboardBtn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('loggedInUser');
            window.location.href = '../html/Login.html';
        });
    }

    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!localStorage.getItem('loggedInUser')) {
                alert('Bạn cần đăng nhập HR để truy cập Dashboard!');
                window.location.href = '../html/Login.html';
                return;
            }
            window.location.href = 'Create_job.html';
        });
    }
}
// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const headerOffset = 70;
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});
// Check login status and update UI
function checkLoginStatus() {
    const user = localStorage.getItem('loggedInUser');
    console.log('Checking login status, user:', user); // Debug log
    
    if (user) {
        console.log('User is logged in:', user);
        // Hiển thị tên user trong header
        const loginBtn = document.querySelector('.login-btn');
        console.log('Found login button:', loginBtn); // Debug log
        
        if (loginBtn) {
            loginBtn.textContent = user;
            loginBtn.href = '#';
            loginBtn.onclick = null; // Loại bỏ onclick handler cũ
            
            // Thêm event listener cho dropdown
            const userMenu = document.querySelector('.user-menu');
            if (userMenu) {
                userMenu.addEventListener('mouseenter', function() {
                    this.classList.add('active');
                });
                
                userMenu.addEventListener('mouseleave', function() {
                    this.classList.remove('active');
                });
            }
            
            console.log('Updated login button text to:', user); // Debug log
        }
    } else {
        console.log('No user logged in, showing login button');
        // Không làm gì cả, để hiển thị "Đăng nhập HR" như bình thường
    }
}
// Animate on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards and sections
document.querySelectorAll('.highlight-card, .info-card, .about-content').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease-out';
    observer.observe(el);
});

// Highlight cards hover effect
document.querySelectorAll('.highlight-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.borderLeft = '4px solid #2563eb';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.borderLeft = 'none';
    });
});

// Social icons click handler
document.querySelectorAll('.social-icon').forEach(icon => {
    icon.addEventListener('click', function() {
        const title = this.getAttribute('title');
        alert(`Chuyển đến trang ${title} của HireSmart`);
        // Trong thực tế, thay bằng link thật:
        // window.open('https://facebook.com/HireSmart', '_blank');
    });
});

// Initialize page when loaded
window.addEventListener('load', function() {
    // Add loading animation
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
    
    // Initialize language system
    initializeLanguage();
    
    // Initialize user authentication
    initializeUserAuth();
    checkLoginStatus();
});

// Mobile menu toggle (for responsive)
const createMobileMenu = () => {
    if (window.innerWidth <= 768) {
        const nav = document.querySelector('nav');
        const menuBtn = document.createElement('div');
        menuBtn.innerHTML = '☰';
        menuBtn.style.cssText = `
            font-size: 2rem;
            cursor: pointer;
            display: none;
        `;
        
        if (window.innerWidth <= 768) {
            menuBtn.style.display = 'block';
            const menu = document.querySelector('.nav-menu');
            
            menuBtn.addEventListener('click', () => {
                menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
                menu.style.flexDirection = 'column';
                menu.style.position = 'absolute';
                menu.style.top = '70px';
                menu.style.right = '0';
                menu.style.background = 'white';
                menu.style.padding = '1rem';
                menu.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
            });
        }
    }
};

// Parallax effect for hero
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const heroSlider = document.querySelector('.hero-slider');
    if (heroSlider && scrolled < 600) {
        heroSlider.style.transform = `translateY(${scrolled * 0.5}px)`;
    }
});

// Counter animation for statistics (if needed)
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start);
        }
    }, 16);
}

// Log page view (for analytics)
console.log('HireSmart Home Page Loaded');
console.log('User Agent:', navigator.userAgent);
console.log('Screen Resolution:', window.screen.width + 'x' + window.screen.height);