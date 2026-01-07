// UI Utilities and Interactions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initSmoothScrolling();
    initNavbarEffects();
    initCounters();
    initPlanCards();
    initRegisterForm();
    initAlertSystem();
    initLazyLoading();
    initBackToTop();
    initTooltips();
    initUserProfileBox();
});

// ================= UTILITY FUNCTIONS =================

function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(targetId);
            if (!target) return;
            
            const offset = 80; // Navbar height
            const targetPosition = target.getBoundingClientRect().top + window.pageYOffset;
            
            window.scrollTo({
                top: targetPosition - offset,
                behavior: 'smooth'
            });
            
            // Update active nav link
            if (targetId !== '#home') {
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === targetId) {
                        link.classList.add('active');
                    }
                });
            }
        });
    });
}

function initNavbarEffects() {
    const navbar = document.querySelector('.custom-navbar');
    if (!navbar) return;
    
    // Scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        updateActiveNav();
    });
    
    // Active nav update
    function updateActiveNav() {
        const sections = document.querySelectorAll('section[id]');
        const scrollPos = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }
}

function initCounters() {
    const counters = document.querySelectorAll('.counter');
    if (counters.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = +counter.getAttribute('data-count');
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;
                
                const updateCounter = () => {
                    current += step;
                    if (current < target) {
                        counter.textContent = Math.ceil(current);
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target;
                    }
                };
                
                updateCounter();
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => observer.observe(counter));
}

function initHeroButton() {
    const heroBtn = document.getElementById('btn-join-now');
    
    if (heroBtn) {
        heroBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Mencegah aksi default link
            
            const targetSection = document.querySelector('#plans');
            if (targetSection) {
                // Lakukan scroll halus
                targetSection.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    }
}

function initPlanCards() {
    const planCards = document.querySelectorAll('.plan-card');
    planCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-15px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function initRegisterForm() {
    const registerForm = document.querySelector('#registerModal form');
    if (!registerForm) return;
    
    registerForm.addEventListener('submit', function(e) {
        const password = this.querySelector('input[name="password"]');
        const terms = this.querySelector('#termsCheck');
        
        if (password.value.length < 6) {
            e.preventDefault();
            showAlert('Password minimal 6 karakter!', 'error');
            password.focus();
            return;
        }
        
        if (!terms.checked) {
            e.preventDefault();
            showAlert('Anda harus menyetujui Syarat & Ketentuan!', 'error');
            terms.focus();
            return;
        }
        
        showAlert('Pendaftaran sedang diproses...', 'success');
    });
}

function initAlertSystem() {
    window.showAlert = function(message, type = 'info') {
        // Remove existing alert
        const existingAlert = document.querySelector('.custom-alert');
        if (existingAlert) existingAlert.remove();
        
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `custom-alert alert-${type}`;
        alertDiv.innerHTML = `
            <div class="alert-content">
                <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : type === 'error' ? 'bi-exclamation-circle-fill' : 'bi-info-circle-fill'} me-2"></i>
                ${message}
            </div>
        `;
        
        // Add styles
        alertDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 9999;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            animation: slideIn 0.3s ease;
            max-width: 400px;
        `;
        
        document.body.appendChild(alertDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            alertDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    };
    
    // Add CSS for animations only once
    if (!document.querySelector('#alert-styles')) {
        const style = document.createElement('style');
        style.id = 'alert-styles';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    if (images.length === 0) return;
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

function initBackToTop() {
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '<i class="bi bi-chevron-up"></i>';
    backToTop.className = 'back-to-top';
    backToTop.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 50%;
        display: none;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        cursor: pointer;
        z-index: 100;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(220, 53, 69, 0.3);
    `;
    
    document.body.appendChild(backToTop);
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.style.display = 'flex';
        } else {
            backToTop.style.display = 'none';
        }
    });
}

function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ================= USER PROFILE BOX =================

function initUserProfileBox() {
    // Hover effect for stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.2}s`;
        
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Handle long package names
    const packageValueElements = document.querySelectorAll('.package-card .stat-value');
    packageValueElements.forEach(element => {
        const packageName = element.textContent.trim();
        
        // Cek jika nama paket panjang (lebih dari 8 karakter)
        if (packageName.length > 8) {
            // Tambah class untuk styling khusus
            element.classList.add('long-text');
            
            // Adjust font size berdasarkan panjang teks
            if (packageName.length > 12) {
                element.style.fontSize = '1.3rem';
            } else if (packageName.length > 10) {
                element.style.fontSize = '1.4rem';
            }
        }
        
        // Truncate jika sangat panjang
        if (packageName.length > 15) {
            element.textContent = packageName.substring(0, 12) + '...';
        }
    });
    
    // Click effect for buttons (ripple effect)
    const profileButtons = document.querySelectorAll('.btn-upgrade, .btn-profile');
    profileButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.7);
                transform: scale(0);
                animation: ripple 0.6s linear;
                width: ${size}px;
                height: ${size}px;
                top: ${y}px;
                left: ${x}px;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
                this.style.position = '';
                this.style.overflow = '';
            }, 600);
        });
    });
    
    // Add ripple animation CSS
    if (!document.querySelector('#ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Special effect for Pro users
    const packageValue = document.querySelector('.package-card .stat-value');
    if (packageValue) {
        const packageText = packageValue.textContent.trim().toLowerCase();
        if (packageText === 'pro' || packageText.includes('pro')) {
            const packageCard = packageValue.closest('.stat-card');
            
            // Add glowing effect style
            if (!document.querySelector('#pro-glow-styles')) {
                const style = document.createElement('style');
                style.id = 'pro-glow-styles';
                style.textContent = `
                    @keyframes proGlow {
                        0%, 100% { 
                            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
                            border-color: var(--gold-color) !important;
                        }
                        50% { 
                            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
                            border-color: var(--gold-color) !important;
                        }
                    }
                    
                    .pro-user-glow {
                        animation: proGlow 2s infinite;
                    }
                    
                    .pro-user-glow .stat-value {
                        color: var(--gold-color) !important;
                    }
                `;
                document.head.appendChild(style);
            }
            
            packageCard.classList.add('pro-user-glow');
        }
    }
}

// Social Media Click Tracking
function initSocialMediaTracking() {
    const socialLinks = document.querySelectorAll('.social-icon, .social-icon-sm, .footer-links a[href*="http"]');
    
    socialLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const platform = this.getAttribute('title') || 
                           this.querySelector('i').className.split(' ')[1] || 
                           'unknown';
            const url = this.href;
            
            // Log social media click (you can send to analytics here)
            console.log(`Social media clicked: ${platform} - ${url}`);
            
            // Optional: Send to Google Analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'social_click', {
                    'event_category': 'Social Media',
                    'event_label': platform,
                    'transport_type': 'beacon'
                });
            }
            
            // Open in new tab (already handled by target="_blank")
            // Continue with default behavior
        });
    });
    
    // Contact links tracking
    const contactLinks = document.querySelectorAll('a[href^="tel:"], a[href^="mailto:"]');
    contactLinks.forEach(link => {
        link.addEventListener('click', function() {
            const type = this.href.startsWith('tel:') ? 'phone' : 'email';
            console.log(`${type} contact clicked: ${this.href}`);
            
            if (typeof gtag !== 'undefined') {
                gtag('event', 'contact_click', {
                    'event_category': 'Contact',
                    'event_label': type,
                    'transport_type': 'beacon'
                });
            }
        });
    });
}

// Update DOMContentLoaded to include social media tracking
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initializations ...
    initSocialMediaTracking();
    // ... rest of code ...
});