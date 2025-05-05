import React, { useState, useEffect } from 'react';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: React.ReactNode;
  description: JSX.Element;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Enterprise Security',
    icon: (
      <svg className="featureIcon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 4c1.86 0 3.41 1.28 3.86 3H8.14c.45-1.72 2-3 3.86-3zm0 14c-2.99 0-5.73-1.47-7.4-3.85A6.08 6.08 0 007 14h10c.7.91 1.16 2 1.4 3.15A9.98 9.98 0 0112 19zm7-9h-2.07a8.03 8.03 0 01-1.58 3H5.65a8.03 8.03 0 01-1.58-3H2V6.81l10-4.5 10 4.5V10h-3z" />
      </svg>
    ),
    description: (
      <>
        Manage alerts, incidents, and observables with sophisticated SOAR capabilities.
        Complete data isolation by company with robust RBAC.
      </>
    ),
  },
  {
    title: 'RESTful API',
    icon: (
      <svg className="featureIcon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M20 4c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2h16zm0 14V8H4v10h16zM6 16h2v-2H6v2zm0-4h8v-2H6v2zm10 0h2v-2h-2v2zm-6 4h8v-2h-8v2z"/>
      </svg>
    ),
    description: (
      <>
        Seamless integration with your security stack through our comprehensive REST API.
        Detailed documentation and SDKs to streamline development.
      </>
    ),
  },
  {
    title: 'Advanced Analytics',
    icon: (
      <svg className="featureIcon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M8 17h2v-7H8v7zm4 0h2V7h-2v10zm4 0h2v-4h-2v4zm3 2H5c-.55 0-1-.45-1-1V6c0-.55.45-1 1-1h14c.55 0 1 .45 1 1v12c0 .55-.45 1-1 1zM5 3h14c1.66 0 3 1.34 3 3v12c0 1.66-1.34 3-3 3H5c-1.66 0-3-1.34-3-3V6c0-1.66 1.34-3 3-3z"/>
      </svg>
    ),
    description: (
      <>
        Gain real-time insights through dynamic metrics and visualizations.
        Track all system actions with detailed audit logs and reporting.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`${styles.feature} ${isVisible ? styles.visible : ''}`}>
      <div className={styles.featureIcon}>
        {icon}
        <div className={styles.featureIconGlow}></div>
      </div>
      <div className="text--center">
        <h3 className={styles.featureTitle}>{title}</h3>
        <p className={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className={styles.glowOrbs}>
        <div className={styles.glowOrb} style={{left: '10%', top: '20%', animationDelay: '0s'}}></div>
        <div className={styles.glowOrb} style={{right: '15%', top: '30%', animationDelay: '2s'}}></div>
        <div className={styles.glowOrb} style={{left: '20%', bottom: '20%', animationDelay: '4s'}}></div>
      </div>
      <div className="container">
        <h2 className={styles.sectionTitle}>Enterprise-Grade Features</h2>
        <div className={styles.featuresGrid}>
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
