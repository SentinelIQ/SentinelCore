import React, { useEffect, useRef, useState } from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  const [isVisible, setIsVisible] = useState(false);
  const headerRef = useRef(null);

  useEffect(() => {
    setIsVisible(true);
    
    // Parallax effect on scroll
    const handleScroll = () => {
      if (headerRef.current) {
        const scrollPos = window.scrollY;
        headerRef.current.style.backgroundPosition = `center ${scrollPos * 0.05}px`;
      }
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`hero ${styles.heroBanner} ${isVisible ? styles.visible : ''}`} ref={headerRef}>
      <div className={styles.heroBackground}>
        <div className={styles.glowCircle}></div>
        <div className={styles.gridLines}></div>
      </div>
      <div className={styles.particles}>
        {[...Array(15)].map((_, i) => (
          <div 
            key={i} 
            className={styles.particle}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              width: `${Math.random() * 6 + 2}px`,
              height: `${Math.random() * 6 + 2}px`,
            }}
          ></div>
        ))}
      </div>
      <div className="container">
        <div className={styles.logoContainer}>
          <img
            className={styles.logo}
            src="/img/logo.svg"
            alt="SentinelIQ Logo"
            width={100}
            height={100}
          />
          <div className={styles.logoGlow}></div>
        </div>
        <h1 className={`hero__title ${styles.title}`} data-text={siteConfig.title}>{siteConfig.title}</h1>
        <p className={`hero__subtitle ${styles.subtitle}`}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className={`button button--primary button--lg ${styles.buttonPrimary}`}
            to="/docs/intro">
            <span className={styles.buttonText}>Get Started</span>
            <span className={styles.buttonShine}></span>
          </Link>
          <Link
            className={`button button--outline button--lg ${styles.buttonOutline}`}
            to="/docs/api">
            <span className={styles.buttonText}>API Reference</span>
            <span className={styles.buttonShine}></span>
          </Link>
        </div>
        <div className={styles.scrollIndicator}>
          <span className={styles.mouse}>
            <span className={styles.scroll}></span>
          </span>
          <p className={styles.scrollText}>Scroll Down</p>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  
  return (
    <Layout
      title={siteConfig.title}
      description="Enterprise-grade platform for security orchestration, automation, and response">
      <HomepageHeader />
      <main className={styles.main}>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
