import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let registered = false;

export function initGsap(): boolean {
    if (!registered) {
        gsap.registerPlugin(ScrollTrigger);
        registered = true;
    }
    if (typeof window === "undefined") return true;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function animateStaggerIn(
    elements: Array<Element | null>,
    options?: { delay?: number; y?: number; duration?: number },
): void {
    const valid = elements.filter(Boolean) as Element[];
    if (!valid.length) return;
    gsap.fromTo(
        valid,
        { opacity: 0, y: options?.y ?? 18 },
        {
            opacity: 1,
            y: 0,
            duration: options?.duration ?? 0.55,
            stagger: 0.1,
            delay: options?.delay ?? 0,
            ease: "power2.out",
        },
    );
}

export function animateRevealOnScroll(
    element: Element | null,
    start = "top 85%",
): void {
    if (!element) return;
    gsap.fromTo(
        element,
        { opacity: 0, y: 22 },
        {
            opacity: 1,
            y: 0,
            duration: 0.55,
            ease: "power2.out",
            scrollTrigger: {
                trigger: element,
                start,
                toggleActions: "play none none reverse",
            },
        },
    );
}
