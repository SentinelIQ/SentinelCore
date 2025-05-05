/**
 * SentinelIQ Enterprise Documentation JavaScript
 * Provides interactive features for the documentation
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all interactive features
  initializeSectionLinks();
  initializeFeedbackSystem();
  initializeCodeCopy();
  
  // Add mobile menu improvements
  if (window.innerWidth <= 960) {
    improveMobileExperience();
  }
});

/**
 * Makes heading sections linkable and provides visual feedback
 */
function initializeSectionLinks() {
  const headings = document.querySelectorAll('h2, h3, h4, h5, h6');
  
  headings.forEach(heading => {
    // Only process headings with IDs
    if (!heading.id) return;
    
    heading.classList.add('linkable-header');
    
    // Add click handler to copy link
    heading.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Create the full URL with hash
      const url = window.location.href.split('#')[0] + '#' + this.id;
      
      // Copy to clipboard
      navigator.clipboard.writeText(url).then(() => {
        // Visual feedback
        const originalTitle = this.getAttribute('title') || '';
        this.setAttribute('title', 'Link copied to clipboard!');
        
        // Add a temporary visual indicator
        this.classList.add('link-copied');
        
        // Reset after animation
        setTimeout(() => {
          this.classList.remove('link-copied');
          
          if (originalTitle) {
            this.setAttribute('title', originalTitle);
          } else {
            this.removeAttribute('title');
          }
        }, 2000);
      });
    });
    
    // Add tooltip if not already present
    if (!heading.getAttribute('title')) {
      heading.setAttribute('title', 'Click to copy link to this section');
    }
    
    // Add visual indicator
    const linkIcon = document.createElement('span');
    linkIcon.classList.add('header-link-icon');
    linkIcon.innerHTML = ' <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>';
    linkIcon.style.opacity = '0';
    linkIcon.style.transition = 'opacity 0.2s';
    
    heading.appendChild(linkIcon);
    
    // Show/hide link icon on hover
    heading.addEventListener('mouseenter', () => {
      linkIcon.style.opacity = '0.5';
    });
    
    heading.addEventListener('mouseleave', () => {
      linkIcon.style.opacity = '0';
    });
  });
  
  // Handle directly navigating to a hash
  if (window.location.hash) {
    const targetElement = document.getElementById(window.location.hash.substring(1));
    if (targetElement) {
      setTimeout(() => {
        targetElement.classList.add('highlight-section');
        setTimeout(() => {
          targetElement.classList.remove('highlight-section');
        }, 2000);
      }, 500);
    }
  }
}

/**
 * Adds feedback system at the bottom of content pages
 */
function initializeFeedbackSystem() {
  // Only add to content pages, not to the homepage or index pages
  const contentMain = document.querySelector('.md-content__inner');
  if (!contentMain || document.querySelector('.md-content__inner > h1')?.textContent === 'Home') {
    return;
  }
  
  // Create feedback container
  const feedbackContainer = document.createElement('div');
  feedbackContainer.classList.add('feedback-container');
  
  const feedbackText = document.createElement('p');
  feedbackText.textContent = 'Was this page helpful?';
  
  const buttonsContainer = document.createElement('div');
  buttonsContainer.classList.add('feedback-buttons');
  
  // Create thumbs up button
  const thumbsUpButton = document.createElement('button');
  thumbsUpButton.classList.add('feedback-button');
  thumbsUpButton.innerHTML = '👍 Yes';
  thumbsUpButton.setAttribute('aria-label', 'Yes, this page was helpful');
  
  // Create thumbs down button
  const thumbsDownButton = document.createElement('button');
  thumbsDownButton.classList.add('feedback-button');
  thumbsDownButton.innerHTML = '👎 No';
  thumbsDownButton.setAttribute('aria-label', 'No, this page was not helpful');
  
  // Add event listeners
  thumbsUpButton.addEventListener('click', () => {
    provideFeedback(true);
    thumbsUpButton.classList.add('feedback-button--selected');
    thumbsDownButton.classList.remove('feedback-button--selected');
  });
  
  thumbsDownButton.addEventListener('click', () => {
    provideFeedback(false);
    thumbsDownButton.classList.add('feedback-button--selected');
    thumbsUpButton.classList.remove('feedback-button--selected');
  });
  
  // Build and append the feedback system
  buttonsContainer.appendChild(thumbsUpButton);
  buttonsContainer.appendChild(thumbsDownButton);
  
  feedbackContainer.appendChild(feedbackText);
  feedbackContainer.appendChild(buttonsContainer);
  
  // Add to the page
  contentMain.appendChild(feedbackContainer);
}

/**
 * Handles the feedback submission
 * In a real implementation, this would send the feedback to a server
 */
function provideFeedback(isHelpful) {
  const pagePath = window.location.pathname;
  console.log(`Feedback for ${pagePath}: ${isHelpful ? 'Helpful' : 'Not helpful'}`);
  
  // In a real implementation, you would send this data to your server
  // This is just a placeholder
  const feedbackData = {
    page: pagePath,
    isHelpful: isHelpful,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent
  };
  
  // Visual feedback to the user
  const feedbackText = document.querySelector('.feedback-container p');
  if (feedbackText) {
    feedbackText.textContent = 'Thank you for your feedback!';
  }
  
  // You could send this data to your analytics or a dedicated endpoint
  // fetch('/api/feedback', {
  //   method: 'POST',
  //   headers: {
  //     'Content-Type': 'application/json',
  //   },
  //   body: JSON.stringify(feedbackData),
  // });
}

/**
 * Enhances the code blocks with better copy functionality
 */
function initializeCodeCopy() {
  // Material theme has built-in code copy, but we can enhance it
  const codeBlocks = document.querySelectorAll('pre code');
  
  codeBlocks.forEach(codeBlock => {
    // Add a copy button if it doesn't exist yet
    if (!codeBlock.parentElement.querySelector('.code-copy-button')) {
      const copyButton = document.createElement('button');
      copyButton.classList.add('code-copy-button');
      copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
      copyButton.setAttribute('title', 'Copy to clipboard');
      
      copyButton.addEventListener('click', () => {
        const code = codeBlock.textContent;
        navigator.clipboard.writeText(code).then(() => {
          copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
          copyButton.classList.add('copied');
          
          setTimeout(() => {
            copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
            copyButton.classList.remove('copied');
          }, 2000);
        });
      });
      
      codeBlock.parentElement.appendChild(copyButton);
    }
  });
}

/**
 * Improves navigation experience on mobile devices
 */
function improveMobileExperience() {
  // Add a back-to-top button for mobile
  const backToTopButton = document.createElement('button');
  backToTopButton.classList.add('back-to-top');
  backToTopButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"/></svg>';
  backToTopButton.setAttribute('aria-label', 'Back to top');
  
  backToTopButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  
  document.body.appendChild(backToTopButton);
  
  // Show/hide the button based on scroll position
  let scrollTimer;
  window.addEventListener('scroll', () => {
    if (scrollTimer) {
      clearTimeout(scrollTimer);
    }
    
    if (window.scrollY > 300) {
      backToTopButton.classList.add('visible');
    } else {
      backToTopButton.classList.remove('visible');
    }
    
    scrollTimer = setTimeout(() => {
      backToTopButton.classList.add('fade');
    }, 1500);
    
    backToTopButton.classList.remove('fade');
  });
} 