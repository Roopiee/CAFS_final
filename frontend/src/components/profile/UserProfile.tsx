import React from 'react';
import styles from './profile.module.css';

export default function UserProfile() {
    return (
        <div className={styles.container}>
            <main className={styles.mainContainer}>
                
                <div className={styles.pageHeader}>
                    <h1 className={styles.pageTitle}>Profile</h1>
                    <p className={styles.pageSubtitle}>Overview of your verification status and activity.</p>
                </div>

                {/* Candidate Info Block */}
                <div className={styles.candidateInfoBlock} style={{ marginBottom: '2rem' }}>
                    <div className={styles.avatar}>
                            R
                    </div>
                    <div className={styles.candidateDetails}>
                         <div className={styles.candidateNameLarge}>KeyaBRo</div>
                         <div className={styles.candidateDobLarge}>DOB: 28 July 2005</div>
                    </div>
                </div>

                <div className={styles.statsGrid}>
                    
                    <div className={`${styles.statCard} ${styles.cardVerified}`}>
                        <div className={styles.iconCircle}>
                            <svg className={styles.svg} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div className={styles.statLabel}>Verified</div>
                        <div className={styles.statValue}>10</div>
                    </div>

                    <div className={`${styles.statCard} ${styles.cardUnverified}`}>
                        <div className={styles.iconCircle}>
                            <svg className={styles.svg} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        </div>
                        <div className={styles.statLabel}>Unverified</div>
                        <div className={styles.statValue}>5</div>
                    </div>

                    <div className={`${styles.statCard} ${styles.cardPending}`}>
                        <div className={styles.iconCircle}>
                            <svg className={styles.svg} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div className={styles.statLabel}>Pending</div>
                        <div className={styles.statValue}>3</div>
                    </div>

                    <div className={`${styles.statCard} ${styles.totalCard}`}>
                        <div className={styles.statLabel}>Total Certificates</div>
                        <div className={styles.statValue}>18</div>
                    </div>

                </div>

                <div className={styles.tableContainer}>
                    <div className={styles.tableHeader}>
                        <h3 className={styles.tableTitle}>Recent User Activity Logs</h3>
                        <a href="#" className={styles.viewAllBtn}>View All</a>
                    </div>
                    <table className={styles.table}>
                        <thead>
                            <tr className={styles.tr}>
                                <th className={styles.th}>Activity</th>
                                <th className={`${styles.th} ${styles.colDesc}`}>Description</th>
                                <th className={styles.th} style={{ textAlign: 'right' }}>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className={styles.tr}>
                                <td className={`${styles.td} ${styles.colAction}`}>Verified Certificate #8839</td>
                                <td className={`${styles.td} ${styles.colDesc}`}>Advanced AI check completed successfully</td>
                                <td className={`${styles.td} ${styles.colTime}`}>24 mins ago</td>
                            </tr>
                            <tr className={styles.tr}>
                                <td className={`${styles.td} ${styles.colAction}`}>Upload Failed</td>
                                <td className={`${styles.td} ${styles.colDesc}`}>Image resolution too low for processing</td>
                                <td className={`${styles.td} ${styles.colTime}`}>2 hours ago</td>
                            </tr>
                            <tr className={styles.tr}>
                                <td className={`${styles.td} ${styles.colAction}`}>Pending Verification</td>
                                <td className={`${styles.td} ${styles.colDesc}`}>Manual review required for document #3321</td>
                                <td className={`${styles.td} ${styles.colTime}`}>5 hours ago</td>
                            </tr>
                            <tr className={styles.tr}>
                                <td className={`${styles.td} ${styles.colAction}`}>Verified Certificate #1029</td>
                                <td className={`${styles.td} ${styles.colDesc}`}>Instant analysis successful</td>
                                <td className={`${styles.td} ${styles.colTime}`}>1 day ago</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </main>
        </div>
    );
}
