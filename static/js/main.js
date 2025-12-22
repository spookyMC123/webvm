// ═══════════════════════════════════════════════════════════════
// NexoHost Panel - Professional JavaScript
// Made by Joy (@! N!GHT .EXE.</>) by NexoHost
// Powered by InfinityForge
// ═══════════════════════════════════════════════════════════════

$(document).ready(function() {
    // ─────────────────────────────────────────────────────────────
    // Animated Page Load
    // ─────────────────────────────────────────────────────────────
    $('body').css('opacity', '0').animate({ opacity: 1 }, 500);

    // ─────────────────────────────────────────────────────────────
    // Sidebar Toggle for Mobile
    // ─────────────────────────────────────────────────────────────
    const createMobileToggle = () => {
        if ($(window).width() <= 768 && $('.sidebar').length && !$('#mobile-toggle').length) {
            const toggleBtn = $('<button id="mobile-toggle" class="mobile-toggle"><i class="fas fa-bars"></i></button>');
            toggleBtn.css({
                position: 'fixed',
                top: '20px',
                left: '20px',
                zIndex: '1001',
                background: 'linear-gradient(135deg, #0066ff, #00ccff)',
                border: 'none',
                borderRadius: '12px',
                width: '50px',
                height: '50px',
                color: 'white',
                fontSize: '1.5rem',
                cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(0, 102, 255, 0.4)',
                transition: 'all 0.3s ease'
            });
            
            $('body').append(toggleBtn);
            
            toggleBtn.on('click', function() {
                $('.sidebar').toggleClass('active');
                $(this).find('i').toggleClass('fa-bars fa-times');
            });
            
            // Close sidebar when clicking outside
            $(document).on('click', function(e) {
                if (!$(e.target).closest('.sidebar, #mobile-toggle').length) {
                    $('.sidebar').removeClass('active');
                    $('#mobile-toggle i').removeClass('fa-times').addClass('fa-bars');
                }
            });
        }
    };
    
    createMobileToggle();
    $(window).on('resize', createMobileToggle);

    // ─────────────────────────────────────────────────────────────
    // Smooth Scrolling
    // ─────────────────────────────────────────────────────────────
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 800, 'swing');
        }
    });

    // ─────────────────────────────────────────────────────────────
    // Auto-dismiss Alerts
    // ─────────────────────────────────────────────────────────────
    $('.alert').each(function() {
        const alert = $(this);
        setTimeout(() => {
            alert.fadeOut(400, function() {
                $(this).remove();
            });
        }, 5000);
    });

    // ─────────────────────────────────────────────────────────────
    // VPS Stats Auto-Refresh
    // ─────────────────────────────────────────────────────────────
    function refreshVPSStats(vpsId) {
        $.ajax({
            url: `/vps/action/${vpsId}/stats`,
            method: 'POST',
            success: function(response) {
                if (response.success) {
                    const stats = response.stats;
                    $(`#status-${vpsId}`).text(stats.status);
                    $(`#cpu-${vpsId}`).text(stats.cpu);
                    $(`#memory-${vpsId}`).text(stats.memory);
                    $(`#disk-${vpsId}`).text(stats.disk);
                    
                    // Update status badge
                    const statusBadge = $(`#status-badge-${vpsId}`);
                    statusBadge.removeClass('running stopped');
                    if (stats.status === 'Running') {
                        statusBadge.addClass('running');
                    } else {
                        statusBadge.addClass('stopped');
                    }
                }
            }
        });
    }

    // Auto-refresh stats every 30 seconds
    if ($('.vps-card').length) {
        setInterval(() => {
            $('.vps-card').each(function() {
                const vpsId = $(this).data('vps-id');
                if (vpsId) {
                    refreshVPSStats(vpsId);
                }
            });
        }, 30000);
    }

    // ─────────────────────────────────────────────────────────────
    // VPS Action Handlers
    // ─────────────────────────────────────────────────────────────
    $('.vps-action-btn').on('click', function(e) {
        e.preventDefault();
        const btn = $(this);
        const vpsId = btn.data('vps-id');
        const action = btn.data('action');
        
        // Disable button and show loading
        btn.prop('disabled', true);
        const originalHtml = btn.html();
        btn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
        
        $.ajax({
            url: `/vps/action/${vpsId}/${action}`,
            method: 'POST',
            success: function(response) {
                if (response.success) {
                    showNotification('success', response.message);
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showNotification('error', response.message);
                    btn.prop('disabled', false);
                    btn.html(originalHtml);
                }
            },
            error: function() {
                showNotification('error', 'An error occurred. Please try again.');
                btn.prop('disabled', false);
                btn.html(originalHtml);
            }
        });
    });

    // ─────────────────────────────────────────────────────────────
    // Notification System
    // ─────────────────────────────────────────────────────────────
    function showNotification(type, message) {
        const notification = $(`
            <div class="alert alert-${type}" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; animation: slideInRight 0.3s ease-out;">
                ${message}
            </div>
        `);
        
        $('body').append(notification);
        
        setTimeout(() => {
            notification.fadeOut(400, function() {
                $(this).remove();
            });
        }, 4000);
    }

    // ─────────────────────────────────────────────────────────────
    // Form Validation Enhancement
    // ─────────────────────────────────────────────────────────────
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        const originalHtml = submitBtn.html();
        submitBtn.html('<i class="fas fa-spinner fa-spin"></i> Processing...');
        
        // Re-enable after 3 seconds if form doesn't submit
        setTimeout(() => {
            submitBtn.prop('disabled', false);
            submitBtn.html(originalHtml);
        }, 3000);
    });

    // ─────────────────────────────────────────────────────────────
    // Stat Card Hover Effects
    // ─────────────────────────────────────────────────────────────
    $('.stat-card').on('mouseenter', function() {
        $(this).find('.stat-icon').css('transform', 'scale(1.1) rotate(5deg)');
    }).on('mouseleave', function() {
        $(this).find('.stat-icon').css('transform', 'scale(1) rotate(0deg)');
    });

    // ─────────────────────────────────────────────────────────────
    // VPS Card Animations
    // ─────────────────────────────────────────────────────────────
    $('.vps-card').each(function(index) {
        $(this).css({
            opacity: '0',
            transform: 'translateY(30px)'
        }).delay(index * 100).animate({
            opacity: 1
        }, 500, function() {
            $(this).css('transform', 'translateY(0)');
        });
    });

    // ─────────────────────────────────────────────────────────────
    // Particle Background Effect (Optional)
    // ─────────────────────────────────────────────────────────────
    function createParticles() {
        const particleContainer = $('<div class="particles"></div>');
        particleContainer.css({
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            zIndex: -1,
            overflow: 'hidden'
        });
        
        for (let i = 0; i < 50; i++) {
            const particle = $('<div class="particle"></div>');
            const size = Math.random() * 3 + 1;
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * 5;
            
            particle.css({
                position: 'absolute',
                width: size + 'px',
                height: size + 'px',
                background: 'rgba(0, 204, 255, 0.5)',
                borderRadius: '50%',
                left: Math.random() * 100 + '%',
                top: Math.random() * 100 + '%',
                animation: `particleFloat ${duration}s ${delay}s infinite ease-in-out`,
                boxShadow: '0 0 10px rgba(0, 204, 255, 0.5)'
            });
            
            particleContainer.append(particle);
        }
        
        $('body').append(particleContainer);
        
        // Add CSS animation
        if (!$('#particle-animation').length) {
            $('head').append(`
                <style id="particle-animation">
                    @keyframes particleFloat {
                        0%, 100% {
                            transform: translate(0, 0);
                            opacity: 0;
                        }
                        10%, 90% {
                            opacity: 1;
                        }
                        50% {
                            transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px);
                        }
                    }
                </style>
            `);
        }
    }
    
    // Uncomment to enable particles
    // createParticles();

    // ─────────────────────────────────────────────────────────────
    // Copy to Clipboard Function
    // ─────────────────────────────────────────────────────────────
    window.copyToClipboard = function(text) {
        const temp = $('<input>');
        $('body').append(temp);
        temp.val(text).select();
        document.execCommand('copy');
        temp.remove();
        showNotification('success', 'Copied to clipboard!');
    };

    // ─────────────────────────────────────────────────────────────
    // Tooltips
    // ─────────────────────────────────────────────────────────────
    $('[data-tooltip]').each(function() {
        const tooltip = $(this).data('tooltip');
        $(this).on('mouseenter', function(e) {
            const tooltipEl = $(`<div class="tooltip-popup">${tooltip}</div>`);
            tooltipEl.css({
                position: 'fixed',
                background: 'rgba(0, 102, 255, 0.9)',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                zIndex: 10000,
                pointerEvents: 'none',
                boxShadow: '0 4px 15px rgba(0, 102, 255, 0.4)',
                left: e.pageX + 10 + 'px',
                top: e.pageY + 10 + 'px'
            });
            $('body').append(tooltipEl);
        }).on('mouseleave', function() {
            $('.tooltip-popup').remove();
        }).on('mousemove', function(e) {
            $('.tooltip-popup').css({
                left: e.pageX + 10 + 'px',
                top: e.pageY + 10 + 'px'
            });
        });
    });

    // ─────────────────────────────────────────────────────────────
    // Console Welcome Message
    // ─────────────────────────────────────────────────────────────
    console.log('%c╔═══════════════════════════════════════════════════════════════╗', 'color: #00ccff; font-weight: bold;');
    console.log('%c║                    NexoHost Panel                             ║', 'color: #00ccff; font-weight: bold;');
    console.log('%c║              Welcome to NexoHost! Power Your Future!          ║', 'color: #0066ff;');
    console.log('%c║                                                               ║', 'color: #00ccff;');
    console.log('%c║   Made by Joy (@! N!GHT .EXE.</>) by NexoHost                ║', 'color: #00ccff;');
    console.log('%c║   Powered by InfinityForge                                    ║', 'color: #0066ff;');
    console.log('%c╚═══════════════════════════════════════════════════════════════╝', 'color: #00ccff; font-weight: bold;');
});
