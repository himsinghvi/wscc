import { motion } from 'framer-motion'

// Shared motion variants + helpers for expressive, consistent animation.

export const pageVariants = {
  initial: { opacity: 0, y: 14, filter: 'blur(6px)' },
  enter: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.4, ease: [0.22, 0.61, 0.36, 1] } },
  exit: { opacity: 0, y: -10, filter: 'blur(4px)', transition: { duration: 0.22 } },
}

// Stagger container: children using `itemVariants` fade up in sequence.
export const staggerContainer = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
}
export const itemVariants = {
  hidden: { opacity: 0, y: 18, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 260, damping: 24 } },
}

// <Reveal> — a single element that fades/springs up when it mounts.
export function Reveal({ children, delay = 0, className, as = 'div', ...rest }) {
  const C = motion[as] || motion.div
  return (
    <C
      className={className}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 0.61, 0.36, 1] }}
      {...rest}
    >
      {children}
    </C>
  )
}

// <Stagger> + <StaggerItem> — grid/list entrance orchestration.
export function Stagger({ children, className, ...rest }) {
  return (
    <motion.div className={className} variants={staggerContainer} initial="hidden" animate="show" {...rest}>
      {children}
    </motion.div>
  )
}
export function StaggerItem({ children, className, ...rest }) {
  return (
    <motion.div className={className} variants={itemVariants} {...rest}>
      {children}
    </motion.div>
  )
}
