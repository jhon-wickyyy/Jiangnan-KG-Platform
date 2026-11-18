// 空间布局坐标换算：x/y 测绘坐标（米，y 向北）→ 画布像素（y 轴翻转 + 边界自适应居中）
// 返回 (node) => ({x, y})；无坐标节点一律回退到质心（空数据时回退画布中心）
export function computeSpatialLayout(nodes, width, height, pad = 60) {
  const w = width || 1
  const h = height || 1
  const pts = nodes.filter(
    (n) => typeof n.props?.x === 'number' && typeof n.props?.y === 'number'
  )
  if (!pts.length) {
    return () => ({ x: w / 2, y: h / 2 })
  }
  const cx = pts.reduce((s, n) => s + n.props.x, 0) / pts.length
  const cy = pts.reduce((s, n) => s + n.props.y, 0) / pts.length
  const xs = pts.map((p) => p.props.x)
  const ys = pts.map((p) => p.props.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const spanX = Math.max(maxX - minX, 1)
  const spanY = Math.max(maxY - minY, 1)
  const scale = Math.min((w - 2 * pad) / spanX, (h - 2 * pad) / spanY, 6)
  const offX = pad + (w - 2 * pad - spanX * scale) / 2
  const offY = pad + (h - 2 * pad - spanY * scale) / 2
  return (n) => {
    const px = typeof n.props?.x === 'number' ? n.props.x : cx
    const py = typeof n.props?.y === 'number' ? n.props.y : cy
    return { x: offX + (px - minX) * scale, y: offY + (maxY - py) * scale }
  }
}
