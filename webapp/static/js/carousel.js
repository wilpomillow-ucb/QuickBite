let currentSlide = 0;

document.addEventListener('DOMContentLoaded', () => {
    const mealItems = document.querySelectorAll('.meal-list li');
    const popupOverlay = document.querySelector('.popup-overlay'); 
    const popupMessage = document.getElementById('popup-message'); 

    mealItems.forEach((item) => {
        item.addEventListener('click', function () {
            const mealName = item.getAttribute('data-meal-name');
            popupMessage.innerText = `You ate "${mealName}"!`;
            showPopup();
        });
    });

    function showPopup() {
        popupOverlay.classList.add('show');
    }

    popupOverlay.addEventListener('click', (e) => {
        if (e.target.classList.contains('popup-overlay') || e.target.id === 'close-popup') {
            closePopup();
        }
    });

    function closePopup() {
        popupOverlay.classList.remove('show');
    }
});

function showSlide(slideIndex) {
    const carousel = document.querySelector('.carousel');
    const totalSlides = document.querySelectorAll('.carousel-item').length;
    const indicators = document.querySelectorAll('.indicator');

    if (slideIndex >= totalSlides) {
        currentSlide = 0;
    } else if (slideIndex < 0) {
        currentSlide = totalSlides - 1;
    } else {
        currentSlide = slideIndex;
    }

    const translateX = -currentSlide * 100; 
    carousel.style.transform = `translateX(${translateX}%)`;

    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlide);
    });
}

function nextSlide() {
    showSlide(currentSlide + 1);
}

function prevSlide() {
    showSlide(currentSlide - 1);
}

showSlide(2);

// Simulating a user status check (replace this with real logic)
const isPremiumUser = false;

window.onload = function () {
    const thirdPanel = document.querySelector('.locked-panel');

    if (!isPremiumUser) {
        thirdPanel.classList.add('locked-panel');
    } else {
        thirdPanel.classList.remove('locked-panel');
        thirdPanel.style.opacity = 1; 
        thirdPanel.style.pointerEvents = 'auto'; 
        thirdPanel.querySelector('.locked-content').innerHTML = ''; 
    }
};